"""Claude/Anthropic provider implementation with real HTTP transport."""
from __future__ import annotations
import json
import os
import time
import uuid
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_base import BaseProvider, ProviderRequest, ProviderResponse

class ClaudeProvider(BaseProvider):
    """Production Anthropic Messages API provider."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("claude", config)
        cfg = config or {}
        self._api_key = str(cfg.get("api_key") or os.getenv("ANTHROPIC_API_KEY") or "")
        self._base_url = str(cfg.get("base_url") or "https://api.anthropic.com/v1").rstrip("/")
        self._timeout = float(cfg.get("timeout", 60.0))
        self._supported_models = list(cfg.get("supported_models") or ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"])

    def initialize(self) -> bool:
        self._is_initialized = bool(self._api_key)
        self._health_status = "healthy" if self._is_initialized else "unconfigured"
        return self._is_initialized

    def _call(self, messages: List[Dict[str, str]], model: str, request: ProviderRequest) -> ProviderResponse:
        if not self._api_key:
            raise RuntimeError("Anthropic API key is not configured")
        payload: Dict[str, Any] = {"model": model, "max_tokens": request.max_tokens, "messages": messages}
        if request.system_prompt:
            payload["system"] = request.system_prompt
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(f"{self._base_url}/messages", data=data, method="POST", headers={"x-api-key": self._api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        start = time.time()
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            self._metrics["errors"] += 1
            raise RuntimeError(f"Anthropic request failed: {type(exc).__name__}") from exc
        blocks = body.get("content") or []
        content = "".join(str(block.get("text", "")) for block in blocks if block.get("type") == "text")
        if not content.strip():
            self._metrics["errors"] += 1
            raise RuntimeError("Anthropic response contained empty content")
        usage = body.get("usage") or {}
        response = ProviderResponse(content, model, "claude")
        response.request_id = str(body.get("id") or f"claude_{uuid.uuid4().hex}")
        response.usage = {"prompt_tokens": int(usage.get("input_tokens", 0)), "completion_tokens": int(usage.get("output_tokens", 0)), "total_tokens": int(usage.get("input_tokens", 0)) + int(usage.get("output_tokens", 0))}
        response.finish_reason = str(body.get("stop_reason") or "stop")
        response.latency_ms = (time.time() - start) * 1000
        self._metrics["requests"] += 1
        self._metrics["total_tokens"] += response.usage["total_tokens"]
        return response

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        model = request.model or "claude-sonnet-4-20250514"
        messages = list(request.messages or [{"role": "user", "content": request.prompt}])
        return self._call(messages, model, request)

    def chat(self, messages: List[Dict[str, str]], model: str = "") -> ProviderResponse:
        request = ProviderRequest("", model or "claude-sonnet-4-20250514", "claude")
        request.messages = list(messages)
        return self._call(request.messages, request.model, request)

    def is_available(self) -> bool:
        return self._is_initialized and bool(self._api_key)
