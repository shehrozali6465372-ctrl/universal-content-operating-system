"""Cohere provider backed by the Cohere v2 chat API."""
from __future__ import annotations
import json, os, time, uuid, urllib.error, urllib.request
from typing import Any, Dict, List, Optional
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_base import BaseProvider, ProviderRequest, ProviderResponse
class CohereProvider(BaseProvider):
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("cohere",config); cfg=config or {}; self._api_key=str(cfg.get("api_key") or os.getenv("COHERE_API_KEY") or ""); self._base_url=str(cfg.get("base_url") or "https://api.cohere.com/v2").rstrip("/"); self._timeout=float(cfg.get("timeout",60)); self._supported_models=list(cfg.get("supported_models") or ["command-r-plus","command-r"])
    def initialize(self)->bool:
        self._is_initialized=bool(self._api_key); self._health_status="healthy" if self._is_initialized else "unconfigured"; return self._is_initialized
    def _call(self,messages,model,request):
        if not self._api_key: raise RuntimeError("Cohere API key is not configured")
        payload={"model":model,"messages":messages,"temperature":request.temperature,"max_tokens":request.max_tokens}
        req=urllib.request.Request(f"{self._base_url}/chat",data=json.dumps(payload).encode(),method="POST",headers={"Authorization":f"Bearer {self._api_key}","Content-Type":"application/json"})
        start=time.time()
        try:
            with urllib.request.urlopen(req,timeout=self._timeout) as resp: body=json.loads(resp.read().decode())
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,OSError,json.JSONDecodeError) as exc:
            self._metrics["errors"]+=1; raise RuntimeError(f"Cohere request failed: {type(exc).__name__}") from exc
        message=body.get("message") or {}; content="".join(str(x.get("text","")) for x in message.get("content",[]) if x.get("type")=="text")
        if not content.strip(): raise RuntimeError("Cohere response contained empty content")
        usage=body.get("usage") or {}; tokens=usage.get("tokens") or {}
        r=ProviderResponse(content,model,"cohere"); r.request_id=str(body.get("id") or f"cohere_{uuid.uuid4().hex}"); r.usage={"prompt_tokens":int(tokens.get("input_tokens",0)),"completion_tokens":int(tokens.get("output_tokens",0)),"total_tokens":int(tokens.get("input_tokens",0))+int(tokens.get("output_tokens",0))}; r.latency_ms=(time.time()-start)*1000; self._metrics["requests"]+=1; self._metrics["total_tokens"]+=r.usage["total_tokens"]; return r
    def generate(self,request): return self._call(request.messages or [{"role":"user","content":request.prompt}],request.model or "command-r-plus",request)
    def chat(self,messages,model=""):
        request=ProviderRequest("",model or "command-r-plus","cohere"); request.messages=list(messages); return self._call(request.messages,request.model,request)
    def is_available(self)->bool: return self._is_initialized and bool(self._api_key)
