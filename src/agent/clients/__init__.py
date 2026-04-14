"""LLM client factory.

Both backends load models directly into process memory — no servers, no HTTP.

Available backends
------------------
llama_cpp       GGUF models via llama-cpp-python.
                CPU-optimised (ARM NEON on Pi 5). Recommended for Pi 5.
                Install: pip install llama-cpp-python
                Models:  GGUF files downloaded with scripts/download_model.py

transformers    HuggingFace safetensors models via transformers + torch.
                Better on GPU. Slower on CPU-only hardware.
                Install: pip install transformers accelerate
                         pip install torch --index-url …/whl/cpu

Adding a new backend
--------------------
1. Create src/agent/clients/<name>_client.py implementing BaseLLMClient.
2. Add a singleton getter get_<name>_client() in that module.
3. Add a branch in create_llm_client() below.
"""

from __future__ import annotations

from src.agent.clients.base import BaseLLMClient


def create_llm_client() -> BaseLLMClient:
    """Return the configured LLM client (singleton per backend)."""
    from src.config import settings

    backend = settings.llm_backend.lower()

    if backend == "llama_cpp":
        from src.agent.clients.llama_cpp_client import get_llama_cpp_client

        return get_llama_cpp_client()

    if backend == "transformers":
        from src.agent.clients.transformers_client import get_transformers_client

        return get_transformers_client()

    raise ValueError(f"Unknown LLM_BACKEND '{backend}'. Supported values: llama_cpp, transformers")


__all__ = ["BaseLLMClient", "create_llm_client"]
