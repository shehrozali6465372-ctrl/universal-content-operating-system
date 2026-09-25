"""OpenAI provider with production fail-closed and real transport."""
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
    """OpenAI-compatible provider with no simulated production output."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("openai", config)
        cfg = config or {}
        self._api_key = str(
            cfg.get("api_key") or os.getenv("OPENAI_API_KEY") or ""
        )
        self._base_url = str(
            cfg.get("base_url") or "https://api.openai.com/v1"
        ).rstrip("/")
        self._timeout = float(cfg.get("timeout", 60.0))
        self._supported_models = list(
            cfg.get("supported_models")
            or [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo",
                "o1",
                "o1-mini",
                "o3-mini",
            ]
        )

    @staticmethod
    def _is_production() -> bool:
        return os.getenv("UCOS_ENV", "").strip().lower() == "production"

    def initialize(self) -> bool:
        if not self._api_key and self._is_production():
            self._is_initialized = False
            self._health_status = "unhealthy"
            return False
        self._is_initialized = True
        self._health_status = "healthy" if self._api_key else "simulated"
        return True

    def _call(
        self,
        messages: List[Dict[str, str]],
        model: str,
        request: ProviderRequest,
    ) -> ProviderResponse:
        if not self._api_key:
            if self._is_production():
                raise RuntimeError(
                    "OpenAI provider has no API key; refusing simulated production output"
                )
            tokens = max(10, len(request.prompt.split()) * 2)
            response = ProviderResponse(
                f"[OpenAI/{model}] Simulated for: {request.prompt[:100]}...",
                model,
                "openai",
            )
            response.request_id = f"openai_{uuid.uuid4().hex}"
            response.usage = {
                "prompt_tokens": tokens,
                "completion_tokens": tokens * 2,
                "total_tokens": tokens * 3,
            }
            self._metrics["requests"] += 1
            self._metrics["total_tokens"] += response.usage["total_tokens"]
            return response

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if request.stop:
            payload["stop"] = request.stop
        data = json.dumps(payload).encode("utf-8")
        http_request = urllib.request.Request(
            f"{self._base_url}/chat/completions",
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )
        start = time.time()
        try:
            with urllib.request.urlopen(
                http_request, timeout=self._timeout
            ) as http_response:
                body = json.loads(http_response.read().decode("utf-8"))
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            OSError,
            json.JSONDecodeError,
        ) as exc:
            self._metrics["errors"] += 1
            self._health_status = "degraded"
            raise RuntimeError(
                f"OpenAI request failed: {type(exc).__name__}"
            ) from exc

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
        response.request_id = str(
            body.get("id") or f"openai_{uuid.uuid4().hex}"
        )
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
        if not self._is_initialized:
            raise RuntimeError("OpenAI provider is not initialized")
        model = request.model or "gpt-4o-mini"
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
        request = ProviderRequest("", model or "gpt-4o-mini", "openai")
        request.messages = list(messages)
        return self.generate(request)

    def is_available(self) -> bool:
        return self._is_initialized and (
            bool(self._api_key) or not self._is_production()
        )
