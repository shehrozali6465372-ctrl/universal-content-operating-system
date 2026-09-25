"""DeepSeek provider implementation with real HTTP transport."""
from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
from layers.layer12_ai_foundation.modules.model_provider_framework.openai_provider import OpenAIProvider

class DeepSeekProvider(OpenAIProvider):
    """DeepSeek uses an OpenAI-compatible chat-completions API."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        cfg = dict(config or {})
        cfg.setdefault("api_key", os.getenv("DEEPSEEK_API_KEY", ""))
        cfg.setdefault("base_url", "https://api.deepseek.com")
        cfg.setdefault("supported_models", ["deepseek-flash", "deepseek-v4-pro"])
        super().__init__(cfg)
        self._name = "deepseek"

    def _call(self, messages: List[Dict[str, str]], model: str, request: Any):
        response = super()._call(messages, model, request)
        response.provider = "deepseek"
        return response

    def generate(self, request: Any):
        request.model = request.model or "deepseek-flash"
        return super().generate(request)

    def chat(self, messages: List[Dict[str, str]], model: str = ""):
        return super().chat(messages, model or "deepseek-flash")
