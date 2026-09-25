"""Mistral provider using the OpenAI-compatible chat API."""
from __future__ import annotations
import os
from typing import Any, Dict, Optional
from layers.layer12_ai_foundation.modules.model_provider_framework.openai_provider import OpenAIProvider
class MistralProvider(OpenAIProvider):
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        cfg=dict(config or {}); cfg.setdefault("api_key",os.getenv("MISTRAL_API_KEY","")); cfg.setdefault("base_url","https://api.mistral.ai/v1"); cfg.setdefault("supported_models",["mistral-large-latest","mistral-small-latest","codestral-latest"])
        super().__init__(cfg); self._name="mistral"
    def _call(self,messages,model,request):
        r=super()._call(messages,model,request); r.provider="mistral"; return r
    def generate(self,request): request.model=request.model or "mistral-large-latest"; return super().generate(request)
    def chat(self,messages,model=""): return super().chat(messages,model or "mistral-large-latest")
