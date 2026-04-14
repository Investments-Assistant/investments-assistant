"""HuggingFace transformers backend — loads models directly from disk or HF Hub.

No server, no HTTP calls. Weights are loaded into process memory; inference
runs in a thread pool so the async event loop stays free.

Best used when you have a GPU (cuda / mps) or prefer HF safetensors format.
For CPU-only inference on a Pi 5, prefer the llama_cpp backend — it uses
quantised GGUF files and ARM-optimised kernels, which are significantly faster.

Install
-------
    # CPU-only torch (much smaller download)
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install transformers accelerate

Tool calling support
--------------------
Works with any instruction model whose tokenizer supports the `tools` parameter
in apply_chat_template (Qwen 2.5, Llama 3.x, Mistral, Gemma 3, Phi-4, …).

Tool calls are parsed from the raw model output using common markup patterns:
    <tool_call>{"name": "...", "arguments": {...}}</tool_call>   (Qwen 2.5, Hermes)
    <|python_tag|>{"name": "...", "parameters": {...}}<|eom_id|>  (Llama 3.1)
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
import json
import re
from typing import Any

from src.agent.clients.base import BaseLLMClient
from src.agent.utils.logger import get_logger
from src.config import settings
from src.tools import dispatch_tool
from src.tools.definitions import TOOL_DEFINITIONS, to_openai_tools

logger = get_logger(__name__)

_TOOLS = to_openai_tools(TOOL_DEFINITIONS)

# Singleton — large model; load once and reuse across all sessions.
_instance: TransformersClient | None = None

# ---------------------------------------------------------------------------
# Tool call parsers — ordered by prevalence
# ---------------------------------------------------------------------------
_TOOL_CALL_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    # (pattern, name_key, input_key)
    # Qwen 2.5, Hermes, many open models
    (
        re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL),
        "name",
        "arguments",
    ),
    # Llama 3.1
    (
        re.compile(r"<\|python_tag\|>(.*?)<\|eom_id\|>", re.DOTALL),
        "name",
        "parameters",
    ),
]


def _parse_tool_calls(text: str) -> tuple[str, list[dict[str, Any]]]:
    """Extract tool calls from raw model output.

    Returns (clean_text, tool_calls) where clean_text has the tool markup
    stripped and tool_calls is a list of {"id", "name", "input"} dicts.
    """
    for pattern, name_key, input_key in _TOOL_CALL_PATTERNS:
        matches = pattern.findall(text)
        if not matches:
            continue

        tool_calls: list[dict[str, Any]] = []
        for i, match in enumerate(matches):
            try:
                tc = json.loads(match)
                tool_calls.append(
                    {
                        "id": f"call_{i}",
                        "name": tc.get(name_key, ""),
                        "input": tc.get(input_key, tc.get("arguments", tc.get("parameters", {}))),
                    }
                )
            except json.JSONDecodeError:
                logger.debug("Could not parse tool call JSON: %r", match)

        if tool_calls:
            clean = pattern.sub("", text).strip()
            return clean, tool_calls

    return text, []


class TransformersClient(BaseLLMClient):
    """In-process HuggingFace model inference via transformers + torch."""

    def __init__(self) -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise ImportError(
                "torch and transformers are required for the transformers backend.\n"
                "Install:\n"
                "  pip install transformers accelerate\n"
                "  pip install torch --index-url https://download.pytorch.org/whl/cpu"
            ) from exc

        model_id = settings.llm_model_name
        device = settings.llm_device

        logger.info("Loading tokenizer: %s", model_id)
        self._tokenizer = AutoTokenizer.from_pretrained(model_id)
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        logger.info("Loading model %s onto %s", model_id, device)
        dtype = torch.float16 if device == "cuda" else torch.float32
        self._model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=dtype,
            device_map=device if device == "cuda" else None,
            low_cpu_mem_usage=True,
        )
        if device != "cuda":
            self._model.to(device)
        self._model.eval()

        self._device = device
        self._torch = torch
        logger.info("Model %s loaded", model_id)

    # ------------------------------------------------------------------
    # Synchronous inference — called inside run_in_executor
    # ------------------------------------------------------------------

    def _run_inference(self, messages: list[dict[str, Any]]) -> str:
        """Tokenise, generate, decode. Runs in a thread pool."""
        try:
            # Prefer the tokenizer's native tool-aware template.
            input_ids = self._tokenizer.apply_chat_template(
                messages,
                tools=_TOOLS,
                add_generation_prompt=True,
                return_tensors="pt",
            ).to(self._device)
        except Exception:
            # Fallback for tokenizers that don't support tools in their template.
            logger.debug("Tokenizer doesn't support tools parameter — falling back")
            input_ids = self._tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                return_tensors="pt",
            ).to(self._device)

        with self._torch.no_grad():
            output_ids = self._model.generate(
                input_ids,
                max_new_tokens=settings.agent_max_tokens,
                temperature=settings.agent_temperature,
                do_sample=settings.agent_temperature > 0,
                pad_token_id=self._tokenizer.eos_token_id,
            )

        # Decode only the newly generated tokens.
        generated_ids = output_ids[0][input_ids.shape[-1] :]
        # skip_special_tokens=False so we can detect tool call markup.
        return self._tokenizer.decode(generated_ids, skip_special_tokens=False).strip()

    # ------------------------------------------------------------------
    # BaseLLMClient interface
    # ------------------------------------------------------------------

    async def stream_response(
        self,
        messages: list[dict[str, Any]],
        system: str,
    ) -> AsyncGenerator[dict, None]:
        loop = asyncio.get_event_loop()
        full_messages: list[dict[str, Any]] = [
            {"role": "system", "content": system},
            *messages,
        ]

        while True:
            raw = await loop.run_in_executor(
                None, lambda msgs=full_messages: self._run_inference(msgs)
            )

            clean_text, tool_calls = _parse_tool_calls(raw)

            if clean_text:
                yield {"type": "text_delta", "text": clean_text}

            # Append assistant turn.
            assistant_msg: dict[str, Any] = {"role": "assistant", "content": clean_text or None}
            if tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["input"]),
                        },
                    }
                    for tc in tool_calls
                ]
            full_messages.append(assistant_msg)

            if not tool_calls:
                yield {"type": "done"}
                break

            # Dispatch tools and feed results back.
            tool_result_messages: list[dict[str, Any]] = []
            for tc in tool_calls:
                yield {
                    "type": "tool_call",
                    "name": tc["name"],
                    "input": tc["input"],
                    "id": tc["id"],
                }
                result_str = await dispatch_tool(tc["name"], tc["input"])
                yield {
                    "type": "tool_result",
                    "name": tc["name"],
                    "result": result_str,
                    "id": tc["id"],
                }
                tool_result_messages.append(
                    {"role": "tool", "tool_call_id": tc["id"], "content": result_str}
                )

            full_messages.extend(tool_result_messages)


def get_transformers_client() -> TransformersClient:
    """Return the singleton TransformersClient, loading the model on first call."""
    global _instance
    if _instance is None:
        _instance = TransformersClient()
    return _instance
