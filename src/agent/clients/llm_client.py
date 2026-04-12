from typing import Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from agent.utils.logger import get_logger
from config import config

logger = get_logger(__name__)


class LLMClient:
    """Simple local LLM client abstraction."""

    def __init__(
        self,
        model: str = "meta-llama/Llama-3.1-8B-Instruct",
        device: str | None = None,
    ):
        logger.info("Initializing LLMClient")
        self.model_name = model
        logger.info("Model: %s", self.model_name)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("Selected device: %s", self.device)
        logger.debug("torch.cuda.is_available(): %s", torch.cuda.is_available())
        self.temperature = config.AGENT_TEMPERATURE
        self.max_tokens = config.AGENT_MAX_TOKENS

        try:
            logger.info("Loading tokenizer for model '%s'", self.model_name)

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            if self.tokenizer.pad_token is None:
                logger.debug(
                    "Tokenizer has no pad_token — setting eos_token as pad_token"
                )
                self.tokenizer.pad_token = self.tokenizer.eos_token

            model_kwargs = {
                "pretrained_model_name_or_path": self.model_name,
            }

            if self.device == "cuda":
                logger.info("Using CUDA with float16 + device_map=auto")
                model_kwargs["torch_dtype"] = torch.float16
                model_kwargs["device_map"] = "auto"
            else:
                logger.info("Using CPU with float32")
                model_kwargs["torch_dtype"] = torch.float32

            logger.info("Loading model weights for '%s'", self.model_name)

            self.llm = AutoModelForCausalLM.from_pretrained(**model_kwargs)

            if self.device != "cuda":
                logger.debug("Moving model to device: %s", self.device)
                self.llm.to(self.device)

            self.llm.eval()

            logger.info("Model '%s' loaded successfully", self.model_name)

        except Exception:
            logger.exception("Failed to initialize model '%s'", self.model_name)
            raise

    def invoke(
        self,
        prompt: str,
        *,
        system_message: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        if model and model != self.model_name:
            raise ValueError(
                "This LLMClient loads the model in __init__. "
                "Instantiate a new LLMClient to use a different model."
            )

        logger.debug(
            "Invoking model '%s' (temperature=%s, max_tokens=%s)",
            self.model_name,
            temperature,
            max_tokens,
        )

        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens if max_tokens is not None else self.max_tokens

        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        if hasattr(self.tokenizer, "apply_chat_template"):
            input_text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        else:
            input_text = self._build_prompt(
                prompt=prompt, system_message=system_message
            )

        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            truncation=True,
        )

        model_device = next(self.llm.parameters()).device
        inputs = {key: value.to(model_device) for key, value in inputs.items()}

        do_sample = temperature > 0
        generation_kwargs = {
            "max_new_tokens": max_tokens,
            "pad_token_id": self.tokenizer.pad_token_id,
            "eos_token_id": self.tokenizer.eos_token_id,
            "do_sample": do_sample,
        }
        if do_sample:
            generation_kwargs["temperature"] = temperature

        with torch.no_grad():
            outputs = self.llm.generate(**inputs, **generation_kwargs)

        prompt_length = inputs["input_ids"].shape[1]
        generated_tokens = outputs[0][prompt_length:]
        response = self.tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True,
        )

        return response.strip()

    @staticmethod
    def _build_prompt(prompt: str, system_message: Optional[str] = None) -> str:
        if system_message:
            return f"System: {system_message}\n\nUser: {prompt}\nAssistant:"
        return f"User: {prompt}\nAssistant:"
