"""deepseek_provider.py — DeepSeek provider implementation."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List, Optional
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_base import BaseProvider, ProviderRequest, ProviderResponse

_REQUEST_ID = itertools.count(1)


class DeepSeekProvider(BaseProvider):
    """DeepSeek AI provider (cost-effective reasoning models)."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("deepseek", config)
        self._supported_models = ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"]
        self._api_key = (config or {}).get("api_key", "")

    def initialize(self) -> bool:
        self._is_initialized = True
        self._health_status = "healthy"
        return True

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        start = time.time()
        req_id = f"deepseek_{next(_REQUEST_ID)}"
        content = f"[DeepSeek/{request.model}] Generated for: {request.prompt[:100]}..."
        tokens = max(10, len(request.prompt.split()) * 2)
        resp = ProviderResponse(content, request.model or "deepseek-chat", "deepseek")
        resp.request_id = req_id
        resp.usage = {"prompt_tokens": tokens, "completion_tokens": tokens * 2, "total_tokens": tokens * 3}
        resp.latency_ms = (time.time() - start) * 1000
        self._metrics["requests"] += 1
        self._metrics["total_tokens"] += resp.usage["total_tokens"]
        return resp

    def chat(self, messages: List[Dict[str, str]], model: str = "") -> ProviderResponse:
        prompt = messages[-1]["content"] if messages else ""
        req = ProviderRequest(prompt, model or "deepseek-chat", "deepseek")
        return self.generate(req)

    def is_available(self) -> bool:
        return self._is_initialized
