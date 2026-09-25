"""Ollama local provider backed by Ollama's REST API."""
from __future__ import annotations
import json, time, uuid, urllib.error, urllib.request
from typing import Any, Dict, List, Optional
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_base import BaseProvider, ProviderRequest, ProviderResponse
class OllamaProvider(BaseProvider):
    def __init__(self,config:Optional[Dict[str,Any]]=None)->None:
        super().__init__("ollama",config); cfg=config or {}; self._base_url=str(cfg.get("base_url") or "http://localhost:11434").rstrip("/"); self._timeout=float(cfg.get("timeout",120)); self._supported_models=list(cfg.get("supported_models") or ["llama3.1","llama3","mistral","qwen2.5","deepseek-r1"])
    def initialize(self)->bool:
        try:
            req=urllib.request.Request(f"{self._base_url}/api/tags",method="GET")
            with urllib.request.urlopen(req,timeout=min(self._timeout,10)): pass
            self._is_initialized=True; self._health_status="healthy"; return True
        except (urllib.error.URLError,TimeoutError,OSError):
            self._is_initialized=False; self._health_status="unavailable"; return False
    def _call(self,messages,model,request):
        payload={"model":model,"messages":messages,"stream":False,"options":{"temperature":request.temperature,"num_predict":request.max_tokens}}
        req=urllib.request.Request(f"{self._base_url}/api/chat",data=json.dumps(payload).encode(),method="POST",headers={"Content-Type":"application/json"})
        start=time.time()
        try:
            with urllib.request.urlopen(req,timeout=self._timeout) as resp: body=json.loads(resp.read().decode())
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,OSError,json.JSONDecodeError) as exc:
            self._metrics["errors"]+=1; raise RuntimeError(f"Ollama request failed: {type(exc).__name__}") from exc
        content=str((body.get("message") or {}).get("content",""))
        if not content.strip(): raise RuntimeError("Ollama response contained empty content")
        r=ProviderResponse(content,model,"ollama"); r.request_id=str(body.get("created_at") or f"ollama_{uuid.uuid4().hex}"); r.latency_ms=(time.time()-start)*1000; self._metrics["requests"]+=1; return r
    def generate(self,request): return self._call(request.messages or [{"role":"user","content":request.prompt}],request.model or "llama3.1",request)
    def chat(self,messages,model=""):
        request=ProviderRequest("",model or "llama3.1","ollama"); request.messages=list(messages); return self._call(request.messages,request.model,request)
    def is_available(self)->bool: return self._is_initialized
