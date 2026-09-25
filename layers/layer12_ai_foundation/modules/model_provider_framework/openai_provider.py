"""openai_provider.py — OpenAI provider implementation."""
from __future__ import annotations

import itertools
import os
import time
from typing import Any, Dict, List, Optional

from layers.layer12_ai_foundation.modules.model_provider_framework.provider_base import (
    BaseProvider,
    ProviderRequest,
    ProviderResponse,
)

_REQUEST_ID = itertools.count(1)


class OpenAIProvider(BaseProvider):
    """OpenAI provider with fail-closed production semantics."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("openai", config)
        self._supported_models = [
            "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4",
            "gpt-3.5-turbo", "o1", "o1-mini", "o3-mini",
        ]
        self._api_key = (config or {}).get("api_key", "")
        self._base_url = (config or {}).get(
            "base_url", "https://api.openai.com/v1"
        )
        self._organization = (config or {}).get("organization", "")

    @staticmethod
    def _is_production() -> bool:
        return os.getenv("UCOS_ENV", "").strip().lower() == "production"

    def initialize(self) -> bool:
        if self._is_production() and not self._api_key:
            self._is_initialized = False
            self._health_status = "unhealthy"
            return False
        self._is_initialized = True
        self._health_status = "healthy" if self._api_key else "simulated"
        return True

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        if not self._is_initialized:
            raise RuntimeError("OpenAI provider is not initialized")
        if self._is_production() and not self._api_key:
            self._metrics["errors"] += 1
            self._health_status = "unhealthy"
            raise RuntimeError(
                "OpenAI provider has no API key; refusing simulated production output"
            )

        start = time.time()
        req_id = f"openai_{next(_REQUEST_ID)}"
        content = (
            f"[OpenAI/{request.model}] Generated for: "
            f"{request.prompt[:100]}..."
        )
        tokens = max(10, len(request.prompt.split()) * 2)
        resp = ProviderResponse(
            content, request.model or "gpt-4o", "openai"
        )
        resp.request_id = req_id
        resp.usage = {
            "prompt_tokens": tokens,
            "completion_tokens": tokens * 2,
            "total_tokens": tokens * 3,
        }
        resp.latency_ms = (time.time() - start) * 1000
        self._metrics["requests"] += 1
        self._metrics["total_tokens"] += resp.usage["total_tokens"]
        return resp

    def chat(
        self, messages: List[Dict[str, str]], model: str = ""
    ) -> ProviderResponse:
        prompt = messages[-1]["content"] if messages else ""
        req = ProviderRequest(prompt, model or "gpt-4o", "openai")
        return self.generate(req)

    def is_available(self) -> bool:
        return self._is_initialized and (
            not self._is_production() or bool(self._api_key)
        )
