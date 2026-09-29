"""APIGateway — Universal REST API for the AI Operating System."""
from __future__ import annotations
import hashlib, hmac, json, logging, os, time, threading, glob
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Any
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

logger = logging.getLogger(__name__)

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
        self._host=host; self._port=port; self._server=None; self._thread=None; self._running=False; self._request_count=0
        self._aios_nonces={}; self._aios_nonce_lock=threading.Lock()
        self._register_routes()
    def _register_routes(self):
        self._routes={"GET /status":self._handle_status,"GET /heartbeat":self._handle_heartbeat,"GET /health":self._handle_health,"GET /healthz":self._handle_healthz,"GET /analytics":self._handle_analytics,"GET /history":self._handle_history,"GET /stats":self._handle_stats,"GET /accounts":self._handle_accounts,"POST /accounts":self._handle_account_create,"POST /generate":self._handle_generate,"POST /v1/jobs":self._handle_aios_job,"GET /templates":self._handle_templates,"GET /platforms":self._handle_platforms,"POST /tiktok/reconcile":self._handle_tiktok_reconcile,"POST /meta/discover":self._handle_meta_discover,"GET /meta/health":self._handle_meta_health,"POST /integrations/atoz/jobs":self._handle_atoz_job,"POST /affiliate/amazon/intake":self._handle_amazon_intake,"GET /browser/health":self._handle_browser_health,"POST /browser/tasks":self._handle_browser_task}
    def _requires_auth(self) -> bool:
        return self._host not in {"127.0.0.1", "localhost", "::1"}
    def _authorized(self, headers: Any) -> bool:
        if not self._requires_auth(): return True
        configured=os.getenv("UCOS_API_TOKEN", "").strip()
        if not configured: return False
        supplied=str(headers.get("Authorization", ""))
        return hmac.compare_digest(supplied, f"Bearer {configured}")

    def _aios_authorized(self, method: str, path: str, raw_body: bytes, headers: Any) -> bool:
        """Verify the AtoZ/AI OS Bridge HMAC transport contract and reject nonce replay."""
        secret=os.getenv("AIOS_API_KEY", "").strip()
        if not secret:
            return False
        try:
            timestamp=str(headers.get("X-AIOS-Timestamp", ""))
            nonce=str(headers.get("X-AIOS-Nonce", ""))
            signature=str(headers.get("X-AIOS-Signature", ""))
            if not timestamp or not nonce or not signature:
                return False
            now=int(time.time())
            ts=int(timestamp)
            if abs(now - ts) > 300:
                return False
            with self._aios_nonce_lock:
                expired=[n for n,t in self._aios_nonces.items() if now-t > 300]
                for n in expired: self._aios_nonces.pop(n, None)
                if nonce in self._aios_nonces:
                    return False
                self._aios_nonces[nonce]=now
            canonical=(f"{method.upper()}\n{path}\n{timestamp}\n{nonce}\n"
                       f"{raw_body.decode('utf-8')}").encode()
            expected=hmac.new(secret.encode("utf-8"), canonical, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, signature)
        except (ValueError, UnicodeDecodeError):
            return False

    def start(self):
        gateway=self
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                gateway._request_count+=1
                parsed=urlparse(self.path); path=parsed.path.rstrip("/")
                if path in {"/heartbeat", "/healthz"}:
                    if not gateway._aios_authorized("GET", path, b"", self.headers):
                        self._send(APIResponse(401,error="AI OS authentication required")); return
                elif not gateway._authorized(self.headers):
                    self._send(APIResponse(401,error="API authentication required")); return
                response=gateway._routes.get(f"GET {path}",lambda p:APIResponse(404,error=f"Endpoint not found: {path}"))(parse_qs(parsed.query)); self._send(response)
            def do_POST(self):
                gateway._request_count+=1
                parsed=urlparse(self.path); path=parsed.path.rstrip("/"); n=int(self.headers.get("Content-Length",0)); raw=self.rfile.read(n) if n else b""
                if path == "/v1/jobs":
                    if not gateway._aios_authorized("POST", path, raw, self.headers):
                        self._send(APIResponse(401,error="AI OS authentication required")); return
                elif not gateway._authorized(self.headers):
                    self._send(APIResponse(401,error="API authentication required")); return
                try:
                    data=json.loads(raw) if raw else {}
                except json.JSONDecodeError:
                    self._send(APIResponse(400,error="Invalid JSON body")); return
                if not isinstance(data, dict):
                    self._send(APIResponse(400,error="JSON body must be an object")); return
                response=gateway._routes.get(f"POST {path}",lambda d:APIResponse(404,error=f"Endpoint not found: {path}"))(data); self._send(response)
            def _send(self,response):
                self.send_response(response.status_code)
                for k,v in response.headers.items(): self.send_header(k,v)
                self.end_headers(); self.wfile.write(response.to_json().encode())
            def log_message(self,format,*args): pass
        try:
            self._server=ThreadingHTTPServer((self._host,self._port),Handler); self._running=True; self._thread=threading.Thread(target=self._server.serve_forever,daemon=True); self._thread.start()
        except OSError as exc: logger.error("API Gateway failed to start on %s:%s: %s", self._host, self._port, exc)
    def stop(self):
        if self._server: self._server.shutdown(); self._running=False
    def is_running(self): return self._running
    def _handle_healthz(self,params):
        return APIResponse(data={"status":"ok","service":"universal-content-operating-system","version":self.VERSION,"layers":self.LAYER_COUNT})

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

    def _handle_heartbeat(self,params):
        return APIResponse(data={"status":"ok","service":"universal-content-operating-system","layer":23,"component":"website_manager"})

    def _handle_amazon_intake(self, data):
        """Accept a product + affiliate link produced by an approved Amazon workflow."""
        try:
            from layers.layer10_monetization.modules.amazon_product_intake import normalize_amazon_product
            required = ("product_name", "product_url", "affiliate_link")
            missing = [key for key in required if not str(data.get(key, "")).strip()]
            if missing:
                return APIResponse(400, error=f"missing required fields: {', '.join(missing)}")
            product = normalize_amazon_product(
                product_name=data["product_name"],
                product_url=data["product_url"],
                affiliate_link=data["affiliate_link"],
                asin=str(data.get("asin", "")),
                niche=str(data.get("niche", "")),
                marketplace=str(data.get("marketplace", "")),
                metadata=dict(data.get("metadata") or {}),
            )
            if not product.tracking_id:
                return APIResponse(400, error="affiliate_link must contain an Amazon Associates tracking tag")
            return APIResponse(status_code=202, data={
                "state": "accepted",
                "source": "amazon_associates_intake",
                "product": product.to_dict(),
                "next": "content_pipeline",
            })
        except (TypeError, ValueError) as exc:
            return APIResponse(400, error=str(exc))
        except Exception as exc:
            logger.exception("Amazon affiliate intake failed")
            return APIResponse(500, error=str(exc))

    def _browser_request(self, method: str, path: str, payload: dict | None = None, timeout: float = 75.0):
        base=os.getenv("UCOS_BROWSER_WORKER_URL", "").strip().rstrip("/")
        token=os.getenv("UCOS_BROWSER_TOKEN", "").strip()
        if not base or not token:
            raise RuntimeError("UCOS browser worker is not configured")
        body=json.dumps(payload or {}).encode("utf-8")
        request=Request(f"{base}{path}", data=body if method != "GET" else None, method=method, headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"})
        try:
            with urlopen(request, timeout=timeout) as response:
                raw=response.read(2_000_000)
                return response.status, json.loads(raw.decode("utf-8"))
        except HTTPError as exc:
            raw=exc.read(2_000_000)
            try: data=json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError): data={"error":str(exc)}
            return exc.code, data
        except URLError as exc:
            raise RuntimeError(f"browser worker unavailable: {exc.reason}") from exc

    def _handle_browser_health(self,params):
        try:
            status, data=self._browser_request("GET", "/health")
            return APIResponse(status_code=200 if status < 400 else 503, data=data if status < 400 else None, error="" if status < 400 else str(data.get("error","browser worker unhealthy")))
        except RuntimeError as exc:
            return APIResponse(status_code=503,error=str(exc))

    def _handle_browser_task(self,data):
        try:
            if not isinstance(data, dict) or not str(data.get("url","")).strip():
                return APIResponse(status_code=400,error="url is required")
            status, result=self._browser_request("POST", "/execute", data)
            if status >= 400:
                return APIResponse(status_code=502 if status >= 500 else 400,error=str(result.get("error","browser task failed")))
            return APIResponse(status_code=202,data={"state":"completed","source":"ucos_personal_browser","result":result.get("result",result)})
        except (RuntimeError, ValueError) as exc:
            return APIResponse(status_code=503,error=str(exc))
        except Exception as exc:
            logger.exception("UCOS browser task dispatch failed")
            return APIResponse(status_code=500,error=str(exc))

    def _handle_aios_job(self,data):
        """AtoZ Product Hub -> AI OS Bridge -> Layer 23 dispatch surface."""
        from layers.layer23_website_manager.integration.atoz_bridge import dispatch_job
        try:
            result=dispatch_job(data)
            return APIResponse(status_code=202,data=result)
        except ValueError as exc:
            return APIResponse(status_code=400,error=str(exc))
        except LookupError as exc:
            return APIResponse(status_code=404,error=str(exc))
        except NotImplementedError as exc:
            return APIResponse(status_code=422,error=str(exc))
        except Exception as exc:
            return APIResponse(status_code=500,error=str(exc))

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
            template_history=[{"template_id":entry.get("template_id"),"template_fingerprint":entry.get("template_fingerprint"),"topic":entry.get("topic"),"platform":entry.get("platform"),"timestamp":entry.get("timestamp")} for entry in history if entry.get("template_id") or entry.get("template_fingerprint")]
            return APIResponse(data={"scope":"account","account_id":account_id,"rankings":template_history,"count":len(template_history)})
        except Exception as exc: return APIResponse(500,error=str(exc))
    def _handle_tiktok_reconcile(self,data):
        account_id=str(data.get("account_id") or "").strip() or None
        try:
            from layers.layer07_publishing.modules.publisher_engine.tiktok_reconciliation_service import TikTokReconciliationService
            return APIResponse(data={"platform":"tiktok","account_id":account_id,"results":TikTokReconciliationService().reconcile(account_id)})
        except (LookupError,ValueError) as exc: return APIResponse(400,error=str(exc))
        except Exception as exc: return APIResponse(500,error=str(exc))
    def _handle_atoz_job(self,data):
        try:
            from layers.layer23_website_manager.integration.atoz_bridge import dispatch_job
            return APIResponse(data=dispatch_job(data))
        except (ValueError,LookupError) as exc:
            return APIResponse(status_code=400,error=str(exc))
        except Exception as exc:
            return APIResponse(status_code=500,error=str(exc))

    def _handle_meta_health(self,params):
        try:
            from layers.layer07_publishing.modules.account_control.meta_asset_discovery import MetaAssetDiscovery
            return APIResponse(data={"provider":"meta","health":MetaAssetDiscovery().health()})
        except RuntimeError as exc:
            return APIResponse(status_code=503,error=str(exc))
        except Exception as exc:
            return APIResponse(status_code=500,error=str(exc))

    def _handle_meta_discover(self,data):
        try:
            from layers.layer14_enterprise_integration.modules.master_orchestrator.control_plane import ControlPlane
            result=ControlPlane().sync_meta_accounts(default_niche=str(data.get("default_niche") or "general"))
            return APIResponse(data=result)
        except (RuntimeError,LookupError,ValueError) as exc: return APIResponse(400,error=str(exc))
        except Exception as exc: return APIResponse(500,error=str(exc))
    def _handle_platforms(self,params):
        return APIResponse(data={"platforms":self.SUPPORTED_PLATFORMS,"production_publishers":["facebook","instagram","pinterest","youtube","tiktok"]})
