"""OpenAI provider implementation with real HTTP transport."""
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


class OpenAIProvider(BaseProvider):
    """Production OpenAI-compatible chat-completions provider."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("openai", config)
        cfg = config or {}
        self._api_key = str(cfg.get("api_key") or os.getenv("OPENAI_API_KEY") or "")
        self._base_url = str(
            cfg.get("base_url") or "https://api.openai.com/v1"
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
                "gpt-4o",
                "gpt-5.6-luna",
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo",
                "o1",
                "o1-mini",
                "o3-mini",
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
            raise RuntimeError("OpenAI API key is not configured")

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if request.stop:
            payload["stop"] = request.stop

        data = json.dumps(payload).encode("utf-8")
        last_error: Optional[BaseException] = None
        start = time.time()

        for attempt in range(self._max_retries + 1):
            req = urllib.request.Request(
                f"{self._base_url}/chat/completions",
                data=data,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
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
            except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
                last_error = exc

            if attempt < self._max_retries:
                time.sleep(min(2 ** attempt, 8))

        if last_error is not None:
            self._metrics["errors"] += 1
            raise RuntimeError(
                f"OpenAI request failed: {type(last_error).__name__}"
            ) from last_error

        choices = body.get("choices") or []
        if not choices:
            self._metrics["errors"] += 1
            raise RuntimeError("OpenAI response contained no choices")
        message = choices[0].get("message") or {}
        content = message.get("content", "")
        if not isinstance(content, str) or not content.strip():
            self._metrics["errors"] += 1
            raise RuntimeError("OpenAI response contained empty content")

        usage = body.get("usage") or {}
        response = ProviderResponse(content, model, "openai")
        response.request_id = str(body.get("id") or f"openai_{uuid.uuid4().hex}")
        response.usage = {
            "prompt_tokens": int(usage.get("prompt_tokens", 0)),
            "completion_tokens": int(usage.get("completion_tokens", 0)),
            "total_tokens": int(usage.get("total_tokens", 0)),
        }
        response.finish_reason = str(
            choices[0].get("finish_reason") or "stop"
        )
        response.latency_ms = (time.time() - start) * 1000
        self._metrics["requests"] += 1
        self._metrics["total_tokens"] += response.usage["total_tokens"]
        return response

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        model = request.model or "gpt-5.6-luna"
        messages: List[Dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.extend(
            request.messages or [{"role": "user", "content": request.prompt}]
        )
        return self._call(messages, model, request)

    def chat(
        self, messages: List[Dict[str, str]], model: str = ""
    ) -> ProviderResponse:
        request = ProviderRequest("", model or "gpt-5.6-luna", "openai")
        request.messages = list(messages)
        return self._call(request.messages, request.model, request)

    def is_available(self) -> bool:
        return self._is_initialized and bool(self._api_key)
