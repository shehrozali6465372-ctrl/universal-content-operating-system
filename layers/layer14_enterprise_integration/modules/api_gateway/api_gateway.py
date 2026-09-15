"""APIGateway — Universal REST API for the AI Operating System."""
from __future__ import annotations
import json, os, time, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, Optional
from urllib.parse import urlparse, parse_qs

class APIResponse:
    __slots__=("status_code","data","error","headers")
    def __init__(self,status_code:int=200,data:Any=None,error:str=""):
        self.status_code=status_code; self.data=data; self.error=error
        self.headers={"Content-Type":"application/json","X-Powered-By":"Universal-AI-OS"}
    def to_json(self)->str:
        body={"success":self.status_code<400,"status":self.status_code}
        if self.data is not None: body["data"]=self.data
        if self.error: body["error"]=self.error
        body["timestamp"]=time.time(); return json.dumps(body,indent=2,default=str)

class APIGateway:
    SUPPORTED_PLATFORMS=["facebook","instagram","linkedin","twitter","youtube","tiktok","pinterest","threads","medium","wordpress","telegram","discord","reddit","binance_square"]
    def __init__(self,host:str="0.0.0.0",port:int=8000):
        self._host=host; self._port=port; self._server=None; self._thread=None; self._running=False; self._request_count=0; self._register_routes()
    def _register_routes(self):
        self._routes={"GET /status":self._handle_status,"GET /health":self._handle_health,"GET /analytics":self._handle_analytics,"GET /history":self._handle_history,"GET /stats":self._handle_stats,"POST /generate":self._handle_generate,"GET /templates":self._handle_templates,"GET /platforms":self._handle_platforms}
    def start(self):
        gateway=self
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                gateway._request_count+=1; parsed=urlparse(self.path); path=parsed.path.rstrip("/"); response=gateway._routes.get(f"GET {path}",lambda p:APIResponse(404,error=f"Endpoint not found: {path}"))(parse_qs(parsed.query)); self._send(response)
            def do_POST(self):
                gateway._request_count+=1; parsed=urlparse(self.path); path=parsed.path.rstrip("/"); n=int(self.headers.get("Content-Length",0)); raw=self.rfile.read(n) if n else b""
                try: data=json.loads(raw) if raw else {}
                except json.JSONDecodeError: data={}
                response=gateway._routes.get(f"POST {path}",lambda d:APIResponse(404,error=f"Endpoint not found: {path}"))(data); self._send(response)
            def _send(self,response):
                self.send_response(response.status_code)
                for k,v in response.headers.items(): self.send_header(k,v)
                self.end_headers(); self.wfile.write(response.to_json().encode())
            def log_message(self,format,*args): pass
        try:
            self._server=HTTPServer((self._host,self._port),Handler); self._running=True; self._thread=threading.Thread(target=self._server.serve_forever,daemon=True); self._thread.start()
        except OSError as exc: print(f"API Gateway failed to start on {self._host}:{self._port}: {exc}")
    def stop(self):
        if self._server: self._server.shutdown(); self._running=False
    def is_running(self): return self._running
    def _handle_status(self,params): return APIResponse(data={"version":"6.0.0","status":"running","gateway_requests":self._request_count,"platforms":self.SUPPORTED_PLATFORMS})
    def _handle_health(self,params):
        checks={"api":"healthy","database":"unknown"}
        try:
            from layers.layer01_core.modules.database_manager import DatabaseManager
            db=DatabaseManager(); db.initialize(); db.health_check(); checks["database"]="healthy"; db.close()
        except Exception: checks["database"]="unavailable"
        checks["gemini"]="configured" if os.environ.get("GEMINI_API_KEY_1","") else "not_configured"
        overall="healthy" if checks["database"]=="healthy" else "degraded"
        return APIResponse(data={"status":overall,"checks":checks})
    def _handle_analytics(self,params):
        try:
            from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_persistence import PipelinePersistence
            p=PipelinePersistence(); data=p.get_analytics_summary(); p.close(); return APIResponse(data={"analytics":data})
        except Exception as exc: return APIResponse(500,error=str(exc))
    def _handle_history(self,params):
        try:
            limit=int(params.get("limit",[10])[0]); platform=params.get("platform",[None])[0]
            from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_persistence import PipelinePersistence
            p=PipelinePersistence(); h=p.get_content_history(platform=platform,limit=limit); p.close(); return APIResponse(data={"history":h,"count":len(h)})
        except Exception as exc: return APIResponse(500,error=str(exc))
    def _handle_stats(self,params):
        try:
            import glob
            layers=sorted(glob.glob("layers/layer*/")); files=sum(len(glob.glob(f"{d}**/*.py",recursive=True)) for d in layers); tests=len(glob.glob("tests/**/test_*.py",recursive=True))
            return APIResponse(data={"version":"6.0.0","layers":len(layers),"source_files":files,"test_files":tests})
        except Exception as exc: return APIResponse(500,error=str(exc))
    def _handle_generate(self,data):
        topic=data.get("topic","artificial intelligence"); platform=data.get("platform"); account_id=data.get("account_id"); tone=data.get("tone","professional"); style=data.get("style","educational"); include_image=bool(data.get("include_image",True))
        try:
            from layers.layer14_enterprise_integration.modules.master_orchestrator.control_plane import ControlPlane
            result=ControlPlane().execute(topic=topic,platform=platform,account_id=account_id,tone=tone,style=style,include_image=include_image)
            return APIResponse(data=result)
        except (LookupError,ValueError) as exc: return APIResponse(400,error=str(exc))
        except Exception as exc: return APIResponse(500,error=str(exc))
    def _handle_templates(self,params):
        try:
            from layers.layer09_learning.modules.prompt_evolution.template_ranker import TemplateRanker
            r=TemplateRanker().get_rankings(platform=params.get("platform",[None])[0]); return APIResponse(data={"rankings":r,"count":len(r)})
        except Exception as exc: return APIResponse(500,error=str(exc))
    def _handle_platforms(self,params):
        return APIResponse(data={"platforms":self.SUPPORTED_PLATFORMS,"production_publishers":["facebook","instagram","pinterest","youtube","tiktok"]})
