"""Google Gemini provider backed by the real Gemini REST API."""
from __future__ import annotations
import json
import os
import time
import uuid
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_base import BaseProvider, ProviderRequest, ProviderResponse

class GeminiProvider(BaseProvider):
    """Production Gemini generateContent adapter."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("gemini", config)
        cfg = config or {}
        self._api_key = str(cfg.get("api_key") or os.getenv("GEMINI_API_KEY") or "")
        self._base_url = str(cfg.get("base_url") or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        self._timeout = float(cfg.get("timeout", 60.0))
        self._supported_models = list(cfg.get("supported_models") or ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"])

    def initialize(self) -> bool:
        self._is_initialized = bool(self._api_key)
        self._health_status = "healthy" if self._is_initialized else "unconfigured"
        return self._is_initialized

    def _call(self, messages: List[Dict[str, str]], model: str, request: ProviderRequest) -> ProviderResponse:
        if not self._api_key:
            raise RuntimeError("Gemini API key is not configured")
        contents = [{"role": ("model" if m.get("role") == "assistant" else "user"), "parts": [{"text": str(m.get("content", ""))}]} for m in messages]
        payload: Dict[str, Any] = {"contents": contents, "generationConfig": {"maxOutputTokens": request.max_tokens, "temperature": request.temperature}}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(f"{self._base_url}/models/{model}:generateContent", data=data, method="POST", headers={"x-goog-api-key": self._api_key, "Content-Type": "application/json"})
        start = time.time()
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            self._metrics["errors"] += 1
            raise RuntimeError(f"Gemini request failed: {type(exc).__name__}") from exc
        candidates = body.get("candidates") or []
        if not candidates:
            self._metrics["errors"] += 1
            raise RuntimeError("Gemini response contained no candidates")
        parts = candidates[0].get("content", {}).get("parts", [])
        content = "".join(str(p.get("text", "")) for p in parts)
        if not content.strip():
            self._metrics["errors"] += 1
            raise RuntimeError("Gemini response contained empty content")
        usage = body.get("usageMetadata") or {}
        response = ProviderResponse(content, model, "gemini")
        response.request_id = str(body.get("responseId") or f"gemini_{uuid.uuid4().hex}")
        response.usage = {"prompt_tokens": int(usage.get("promptTokenCount", 0)), "completion_tokens": int(usage.get("candidatesTokenCount", 0)), "total_tokens": int(usage.get("totalTokenCount", 0))}
        response.finish_reason = str(candidates[0].get("finishReason") or "STOP")
        response.latency_ms = (time.time() - start) * 1000
        self._metrics["requests"] += 1
        self._metrics["total_tokens"] += response.usage["total_tokens"]
        return response

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        model = request.model or "gemini-2.0-flash"
        messages = list(request.messages or [{"role": "user", "content": request.prompt}])
        if request.system_prompt:
            messages = [{"role": "user", "content": request.system_prompt}, {"role": "model", "content": "Understood."}] + messages
        return self._call(messages, model, request)

    def chat(self, messages: List[Dict[str, str]], model: str = "") -> ProviderResponse:
        request = ProviderRequest("", model or "gemini-2.0-flash", "gemini")
        request.messages = list(messages)
        return self._call(request.messages, request.model, request)

    def is_available(self) -> bool:
        return self._is_initialized and bool(self._api_key)
