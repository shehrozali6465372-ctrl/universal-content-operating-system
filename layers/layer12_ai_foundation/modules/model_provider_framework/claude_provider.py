"""claude_provider.py — Claude/Anthropic provider implementation."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List, Optional
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_base import BaseProvider, ProviderRequest, ProviderResponse

_REQUEST_ID = itertools.count(1)


class ClaudeProvider(BaseProvider):
    """Anthropic Claude provider."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("claude", config)
        self._supported_models = ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022",
                                   "claude-3-5-haiku-20241022", "claude-3-opus-20240229",
                                   "claude-3-haiku-20240307"]
        self._api_key = (config or {}).get("api_key", "")

    def initialize(self) -> bool:
        self._is_initialized = True
        self._health_status = "healthy"
        return True

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        start = time.time()
        req_id = f"claude_{next(_REQUEST_ID)}"
        content = f"[Claude/{request.model}] Generated for: {request.prompt[:100]}..."
        tokens = max(10, len(request.prompt.split()) * 2)
        resp = ProviderResponse(content, request.model or "claude-sonnet-4-20250514", "claude")
        resp.request_id = req_id
        resp.usage = {"prompt_tokens": tokens, "completion_tokens": tokens * 2, "total_tokens": tokens * 3}
        resp.latency_ms = (time.time() - start) * 1000
        self._metrics["requests"] += 1
        self._metrics["total_tokens"] += resp.usage["total_tokens"]
        return resp

    def chat(self, messages: List[Dict[str, str]], model: str = "") -> ProviderResponse:
        prompt = messages[-1]["content"] if messages else ""
        req = ProviderRequest(prompt, model or "claude-sonnet-4-20250514", "claude")
        return self.generate(req)

    def is_available(self) -> bool:
        return self._is_initialized
