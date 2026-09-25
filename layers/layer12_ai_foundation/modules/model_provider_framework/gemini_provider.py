"""Google Gemini provider backed by the real Gemini REST API."""
from __future__ import annotations

import json
import os
import time
import uuid
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from layers.layer12_ai_foundation.modules.model_provider_framework.provider_base import (
    BaseProvider,
    ProviderRequest,
    ProviderResponse,
)


class GeminiProvider(BaseProvider):
    """Production Gemini generateContent adapter."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("gemini", config)
        cfg = config or {}
        self._api_key = str(cfg.get("api_key") or os.getenv("GEMINI_API_KEY") or "")
        self._base_url = str(
            cfg.get("base_url")
            or "https://generativelanguage.googleapis.com/v1beta"
        ).rstrip("/")
        self._timeout = float(cfg.get("timeout", 60.0))
        self._max_retries = int(cfg.get("max_retries", 3))
        if self._timeout <= 0:
            raise ValueError("timeout must be positive")
        if self._max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        self._supported_models = list(
            cfg.get("supported_models")
            or [
                "gemini-3.8-flash",
                "gemini-3.7-flash",
                "gemini-3.6-flash",
                "gemini-3.5-flash",
                "gemini-3.5-flash-lite",
                "gemini-2.5-flash",
                "gemini-2.5-pro",
            ]
        )

    def initialize(self) -> bool:
        self._is_initialized = bool(self._api_key)
        self._health_status = (
            "configured" if self._is_initialized else "unconfigured"
        )
        return self._is_initialized

    def _call(
        self,
        messages: List[Dict[str, str]],
        model: str,
        request: ProviderRequest,
    ) -> ProviderResponse:
        if not self._api_key:
            raise RuntimeError("Gemini API key is not configured")

        contents = [
            {
                "role": "model" if m.get("role") == "assistant" else "user",
                "parts": [{"text": str(m.get("content", ""))}],
            }
            for m in messages
        ]
        payload: Dict[str, Any] = {"contents": contents}
        generation_config: Dict[str, Any] = {
            "maxOutputTokens": request.max_tokens
        }
        # Gemini 3.x recommends omitting temperature/top-p/top-k.
        if not model.startswith(("gemini-3.5", "gemini-3.6", "gemini-3.7", "gemini-3.8")):
            generation_config["temperature"] = request.temperature
        payload["generationConfig"] = generation_config
        if request.system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": request.system_prompt}]
            }

        data = json.dumps(payload).encode("utf-8")
        start = time.time()
        last_error: Optional[BaseException] = None

        for attempt in range(self._max_retries + 1):
            req = urllib.request.Request(
                f"{self._base_url}/models/{model}:generateContent",
                data=data,
                method="POST",
                headers={
                    "x-goog-api-key": self._api_key,
                    "Content-Type": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                last_error = None
                break
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code not in (429, 500, 502, 503, 504):
                    break
            except (
                urllib.error.URLError,
                TimeoutError,
                OSError,
                json.JSONDecodeError,
            ) as exc:
                last_error = exc
            if attempt < self._max_retries:
                time.sleep(min(2 ** attempt, 8))

        if last_error is not None:
            self._metrics["errors"] += 1
            raise RuntimeError(
                f"Gemini request failed: {type(last_error).__name__}"
            ) from last_error

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
        response.request_id = str(
            body.get("responseId") or f"gemini_{uuid.uuid4().hex}"
        )
        response.usage = {
            "prompt_tokens": int(usage.get("promptTokenCount", 0)),
            "completion_tokens": int(usage.get("candidatesTokenCount", 0)),
            "total_tokens": int(usage.get("totalTokenCount", 0)),
        }
        response.finish_reason = str(
            candidates[0].get("finishReason") or "STOP"
        )
        response.latency_ms = (time.time() - start) * 1000
        self._metrics["requests"] += 1
        self._metrics["total_tokens"] += response.usage["total_tokens"]
        return response

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        model = request.model or "gemini-3.8-flash"
        messages = list(
            request.messages or [{"role": "user", "content": request.prompt}]
        )
        return self._call(messages, model, request)

    def chat(
        self, messages: List[Dict[str, str]], model: str = ""
    ) -> ProviderResponse:
        request = ProviderRequest("", model or "gemini-3.8-flash", "gemini")
        request.messages = list(messages)
        return self._call(request.messages, request.model, request)

    def is_available(self) -> bool:
        return self._is_initialized and bool(self._api_key)
