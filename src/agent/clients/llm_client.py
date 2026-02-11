"""Lightweight LLM client wrapper used across the repository.

Provides a simple `LLMClient.invoke` method that calls OpenAI's ChatCompletion
API when an API key is available, otherwise falls back to a safe stub.
"""

from typing import Optional, Any

from src.config import config


class LLMClient:
    """Simple LLM client abstraction.

    Example:
            client = LLMClient()
            text = client.invoke("Summarize the following...")
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or config.OPENAI_API_KEY
        self.model = model or config.OPENAI_MODEL

        if self.api_key:
            try:
                import openai  # lazy import to avoid hard dependency at module import time

                openai.api_key = self.api_key
                self._client = openai
            except Exception:
                self._client = None
        else:
            self._client = None

    def invoke(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Invoke the configured LLM and return a plain text response.

        If no OpenAI API key is configured, returns a readable stub response so
        callers don't fail during local development or tests.
        """

        used_model = model or self.model
        temperature = (
            temperature if temperature is not None else config.AGENT_TEMPERATURE
        )
        max_tokens = max_tokens if max_tokens is not None else config.AGENT_MAX_TOKENS

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        if not self._client:
            # Fallback stub for environments without an API key.
            return f"[llm_stub] {prompt}"

        try:
            resp = self._client.ChatCompletion.create(
                model=used_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return self._extract_text_from_response(resp) or ""

        except Exception:  # keep broad catch to let callers handle/retry
            raise

    @staticmethod
    def _extract_text_from_response(resp: Any) -> Optional[str]:
        """Robust extraction of text from OpenAI ChatCompletion responses.

        Handles both dict-like and attribute-style responses returned by
        different OpenAI client versions.
        """
        try:
            # dict-like
            if isinstance(resp, dict):
                choice = resp.get("choices", [None])[0]
                if not choice:
                    return None
                if isinstance(choice, dict):
                    return (choice.get("message", {}) or {}).get(
                        "content"
                    ) or choice.get("text")

            # object-like
            choices = getattr(resp, "choices", None)
            if choices:
                first = choices[0]
                msg = getattr(first, "message", None)
                if msg:
                    return getattr(msg, "content", None)
                return getattr(first, "text", None)

        except Exception:
            return None

        return None
