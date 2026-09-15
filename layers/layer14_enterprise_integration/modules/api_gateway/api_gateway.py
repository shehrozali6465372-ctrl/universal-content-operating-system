"""APIGateway — Universal REST API for the AI Operating System."""
from __future__ import annotations
import json, os, time, threading, glob
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any
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
    VERSION="6.0.0"
    LAYER_COUNT=23
    def __init__(self,host:str="127.0.0.1",port:int=8000):
        self._host=host; self._port=port; self._server=None; self._thread=None; self._running=False; self._request_count=0; self._register_routes()
    def _register_routes(self):
        self._routes={"GET /status":self._handle_status,"GET /health":self._handle_health,"GET /analytics":self._handle_analytics,"GET /history":self._handle_history,"GET /stats":self._handle_stats,"GET /accounts":self._handle_accounts,"POST /accounts":self._handle_account_create,"POST /generate":self._handle_generate,"GET /templates":self._handle_templates,"GET /platforms":self._handle_platforms}
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
    def _handle_status(self,params):
        return APIResponse(data={"version":self.VERSION,"status":"running","layers":self.LAYER_COUNT,"gateway_requests":self._request_count,"platforms":self.SUPPORTED_PLATFORMS})
    def _handle_health(self,params):
        checks={"api":"healthy","database":"unknown"}
        try:
            from layers.layer01_core.modules.database_manager import DatabaseManager
            db=DatabaseManager(); db.initialize(); db.health_check(); checks["database"]="healthy"; db.close()
        except Exception: checks["database"]="unavailable"
        checks["gemini"]="configured" if os.environ.get("GEMINI_API_KEY_1","") else "not_configured"
        overall="healthy" if checks["database"]=="healthy" else "degraded"
        return APIResponse(data={"status":overall,"checks":checks})
    @staticmethod
    def _account_id(params):
        value=params.get("account_id",[None])[0]
        return str(value).strip() if value else None
    def _require_account(self,params):
        account_id=self._account_id(params)
        if not account_id: return None,APIResponse(400,error="account_id is required for account-scoped data")
        from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
        if AccountRegistry().get(account_id) is None: return None,APIResponse(404,error=f"unknown account_id: {account_id}")
        return account_id,None
    def _handle_analytics(self,params):
        try:
            account_id,error=self._require_account(params)
            if error: return error
            from layers.layer07_publishing.modules.account_control.account_data_store import AccountDataStore
            store=AccountDataStore(); values=store.get(account_id,"analytics","collection:execution_outcomes",[])
            return APIResponse(data={"scope":"account","account_id":account_id,"analytics":values,"count":len(values)})
        except Exception as exc: return APIResponse(500,error=str(exc))
    def _handle_history(self,params):
        try:
            account_id,error=self._require_account(params)
            if error: return error
            limit=max(1,min(int(params.get("limit",[10])[0]),1000))
            from layers.layer07_publishing.modules.account_control.account_data_store import AccountDataStore
            store=AccountDataStore(); history=store.get(account_id,"content","collection:execution_history",[])[-limit:][::-1]
            return APIResponse(data={"scope":"account","account_id":account_id,"history":history,"count":len(history)})
        except (TypeError,ValueError) as exc: return APIResponse(400,error=str(exc))
        except Exception as exc: return APIResponse(500,error=str(exc))
    def _handle_stats(self,params):
        try:
            layers=sorted(glob.glob("layers/layer*/")); files=sum(len(glob.glob(f"{d}**/*.py",recursive=True)) for d in layers); tests=len(glob.glob("tests/**/test_*.py",recursive=True))
            return APIResponse(data={"version":self.VERSION,"layers":len(layers),"source_files":files,"test_files":tests})
        except Exception as exc: return APIResponse(500,error=str(exc))
    def _handle_accounts(self,params):
        try:
            from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
            registry=AccountRegistry(); platform=params.get("platform",[None])[0]; enabled=params.get("enabled",["true"])[0].lower()!="false"
            accounts=registry.list(platform=platform,enabled_only=enabled)
            return APIResponse(data={"accounts":[a.__dict__ for a in accounts],"count":len(accounts)})
        except Exception as exc: return APIResponse(500,error=str(exc))
    def _handle_account_create(self,data):
        try:
            from dataclasses import asdict
            from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry, AccountSpec
            required=("account_id","platform","niche")
            missing=[key for key in required if not str(data.get(key,"")).strip()]
            if missing: return APIResponse(400,error=f"missing required fields: {', '.join(missing)}")
            spec=AccountSpec(account_id=str(data["account_id"]),platform=str(data["platform"]),niche=str(data["niche"]),display_name=str(data.get("display_name", "")),audience=str(data.get("audience", "")),credentials_ref=str(data.get("credentials_ref", "")),affiliate_rules=dict(data.get("affiliate_rules") or {}),capabilities=list(data.get("capabilities") or []),constraints=dict(data.get("constraints") or {}),enabled=bool(data.get("enabled",True)))
            workspace=AccountRegistry().register(spec)
            return APIResponse(status_code=201,data={"account":asdict(spec),"workspace":str(workspace),"provisioned_stores":["memory","content","analytics","learning"]})
        except (TypeError,ValueError) as exc: return APIResponse(400,error=str(exc))
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
            account_id,error=self._require_account(params)
            if error: return error
            from layers.layer07_publishing.modules.account_control.account_data_store import AccountDataStore
            store=AccountDataStore(); history=store.get(account_id,"content","collection:execution_history",[])
            template_history=[{"template_id":entry.get("template_id"),"topic":entry.get("topic"),"platform":entry.get("platform"),"timestamp":entry.get("timestamp")} for entry in history if entry.get("template_id")]
            return APIResponse(data={"scope":"account","account_id":account_id,"rankings":template_history,"count":len(template_history)})
        except Exception as exc: return APIResponse(500,error=str(exc))
    def _handle_platforms(self,params):
        return APIResponse(data={"platforms":self.SUPPORTED_PLATFORMS,"production_publishers":["facebook","instagram","pinterest","youtube","tiktok"]})
