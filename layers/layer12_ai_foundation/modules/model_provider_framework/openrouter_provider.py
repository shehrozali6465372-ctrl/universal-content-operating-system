"""OpenRouter provider using its OpenAI-compatible API."""
from __future__ import annotations
import os
from typing import Any, Dict, Optional
from layers.layer12_ai_foundation.modules.model_provider_framework.openai_provider import OpenAIProvider
class OpenRouterProvider(OpenAIProvider):
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        cfg=dict(config or {}); cfg.setdefault("api_key",os.getenv("OPENROUTER_API_KEY","")); cfg.setdefault("base_url","https://openrouter.ai/api/v1"); cfg.setdefault("supported_models",[])
        super().__init__(cfg); self._name="openrouter"
    def _call(self,messages,model,request):
        r=super()._call(messages,model,request); r.provider="openrouter"; return r
    def generate(self,request):
        if not request.model: request.model="openai/gpt-4o-mini"
        return super().generate(request)
    def chat(self,messages,model=""): return super().chat(messages,model or "openai/gpt-4o-mini")
