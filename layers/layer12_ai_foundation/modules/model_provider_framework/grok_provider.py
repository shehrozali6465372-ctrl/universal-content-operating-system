"""xAI Grok provider using xAI's OpenAI-compatible API."""
from __future__ import annotations
import os
from typing import Any, Dict, Optional
from layers.layer12_ai_foundation.modules.model_provider_framework.openai_provider import OpenAIProvider
class GrokProvider(OpenAIProvider):
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        cfg=dict(config or {}); cfg.setdefault("api_key", os.getenv("XAI_API_KEY","")); cfg.setdefault("base_url","https://api.x.ai/v1"); cfg.setdefault("supported_models",["grok-3","grok-3-mini","grok-2"])
        super().__init__(cfg); self._name="grok"
    def _call(self,messages,model,request):
        r=super()._call(messages,model,request); r.provider="grok"; return r
    def generate(self,request): request.model=request.model or "grok-3"; return super().generate(request)
    def chat(self,messages,model=""): return super().chat(messages,model or "grok-3")
