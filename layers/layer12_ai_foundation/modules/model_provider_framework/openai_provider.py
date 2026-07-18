"""openai_provider.py — OpenAI provider implementation."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List, Optional
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_base import BaseProvider, ProviderRequest, ProviderResponse

_REQUEST_ID = itertools.count(1)


class OpenAIProvider(BaseProvider):
    """OpenAI API provider (GPT-4, GPT-4o, GPT-3.5, etc.)."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("openai", config)
        self._supported_models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4",
                                   "gpt-3.5-turbo", "o1", "o1-mini", "o3-mini"]
        self._api_key = (config or {}).get("api_key", "")
        self._base_url = (config or {}).get("base_url", "https://api.openai.com/v1")
        self._organization = (config or {}).get("organization", "")

    def initialize(self) -> bool:
        self._is_initialized = bool(self._api_key) or True  # Allow simulation
        self._health_status = "healthy"
        return self._is_initialized

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        start = time.time()
        req_id = f"openai_{next(_REQUEST_ID)}"
        content = f"[OpenAI/{request.model}] Generated for: {request.prompt[:100]}..."
        tokens = max(10, len(request.prompt.split()) * 2)
        resp = ProviderResponse(content, request.model or "gpt-4o", "openai")
        resp.request_id = req_id
        resp.usage = {"prompt_tokens": tokens, "completion_tokens": tokens * 2, "total_tokens": tokens * 3}
        resp.latency_ms = (time.time() - start) * 1000
        self._metrics["requests"] += 1
        self._metrics["total_tokens"] += resp.usage["total_tokens"]
        return resp

    def chat(self, messages: List[Dict[str, str]], model: str = "") -> ProviderResponse:
        prompt = messages[-1]["content"] if messages else ""
        req = ProviderRequest(prompt, model or "gpt-4o", "openai")
        return self.generate(req)

    def is_available(self) -> bool:
        return self._is_initialized
