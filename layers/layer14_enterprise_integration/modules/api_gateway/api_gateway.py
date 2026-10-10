"""APIGateway — Universal REST API for the AI Operating System."""
from __future__ import annotations
import hashlib, hmac, json, logging, os, time, threading, glob, re
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Any
from urllib.parse import urlparse, parse_qs, urlencode
from datetime import datetime, timezone, timedelta
from base64 import b64encode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

logger = logging.getLogger(__name__)

class PinterestCredentialRefreshError(Exception):
    """Safe, client-facing Pinterest credential refresh failure."""


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
        self._routes={"GET /status":self._handle_status,"GET /heartbeat":self._handle_heartbeat,"GET /health":self._handle_health,"GET /healthz":self._handle_healthz,"GET /analytics":self._handle_analytics,"GET /history":self._handle_history,"GET /stats":self._handle_stats,"GET /accounts":self._handle_accounts,"POST /credentials/pinterest":self._handle_pinterest_credential_store,"POST /credentials/pinterest/revoke":self._handle_pinterest_credential_revoke,"POST /pinterest/operations":self._handle_pinterest_operation,"GET /credentials/pinterest":self._handle_pinterest_credentials,"POST /accounts":self._handle_account_create,"POST /generate":self._handle_generate,"POST /v1/jobs":self._handle_aios_job,"GET /templates":self._handle_templates,"GET /platforms":self._handle_platforms,"POST /tiktok/reconcile":self._handle_tiktok_reconcile,"POST /meta/discover":self._handle_meta_discover,"GET /meta/health":self._handle_meta_health,"POST /integrations/atoz/jobs":self._handle_atoz_job,"POST /affiliate/amazon/intake":self._handle_amazon_intake,"GET /affiliate/amazon/status":self._handle_amazon_browser_status,"POST /affiliate/amazon/search":self._handle_amazon_browser_search,"GET /browser/health":self._handle_browser_health,"POST /browser/tasks":self._handle_browser_task}
    def _requires_auth(self) -> bool:
        return self._host not in {"127.0.0.1", "localhost", "::1"}
    def _authorized(self, headers: Any) -> bool:
        if not self._requires_auth(): return True
        configured_tokens=[v for v in (os.getenv("UCOS_API_TOKEN", "").strip(), os.getenv("UCOS_MLH_SERVICE_TOKEN", "").strip()) if v]
        if not configured_tokens: return False
        supplied=str(headers.get("Authorization", ""))
        return any(hmac.compare_digest(supplied, f"Bearer {token}") for token in configured_tokens)

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
                if path == "/heartbeat":
                    if not gateway._aios_authorized("GET", path, b"", self.headers):
                        self._send(APIResponse(401,error="AI OS authentication required")); return
                elif path != "/healthz" and not gateway._authorized(self.headers):
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
        return APIResponse(status_code=200 if overall == "healthy" else 503, data={"status":overall,"checks":checks})

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

    def _handle_amazon_browser_status(self,params):
        """Return evidence-backed authentication state for an affiliate browser profile."""
        account_ref=str(params.get("account_ref",[""])[0] or "").strip()
        marketplace=str(params.get("marketplace",["www.amazon.com"])[0] or "www.amazon.com").strip().lower()
        if not account_ref:
            return APIResponse(status_code=400,error="account_ref is required")
        if len(account_ref) > 80 or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for ch in account_ref):
            return APIResponse(status_code=400,error="account_ref contains unsafe characters")
        try:
            base=f"https://{marketplace}"
            status_code,result=self._browser_request("POST","/execute",{
                "url":base,
                "profile_ref":account_ref,
                "actions":[{"type":"extract"}],
            })
            if status_code >= 400:
                return APIResponse(status_code=503,error=str(result.get("error","browser worker unavailable")))
            payload=result.get("result",result)
            text=str(payload.get("text",""))
            authenticated=bool(re.search(r"Get Link|SiteStripe|Associates",text,re.I))
            return APIResponse(data={
                "provider":"amazon",
                "account_ref":account_ref,
                "marketplace":marketplace,
                "persistent_profile":bool(payload.get("persistent_profile")),
                "authenticated":authenticated,
                "evidence":{"final_url":payload.get("final_url"),"signals":["amazon_associates_ui"] if authenticated else []},
                "state":"authenticated" if authenticated else "requires_login",
            })
        except Exception as exc:
            return APIResponse(status_code=503,error=str(exc))

    def _handle_amazon_browser_search(self,data):
        """Search Amazon and obtain a real tagged affiliate URL via SiteStripe."""
        account_ref=str(data.get("account_ref","")).strip()
        query=str(data.get("query","")).strip()
        marketplace=str(data.get("marketplace","www.amazon.com") or "www.amazon.com").strip().lower()
        if not account_ref or not query:
            return APIResponse(status_code=400,error="account_ref and query are required")
        try:
            from layers.layer10_monetization.modules.affiliate_browser import AffiliateBrowserClient, AffiliateSearchRequest
            from layers.layer14_enterprise_integration.modules.affiliate_browser_gateway import PersonalBrowserAffiliateGateway
            client=AffiliateBrowserClient(PersonalBrowserAffiliateGateway(self._browser_request))
            link=client.search_and_get_link(AffiliateSearchRequest(
                provider="amazon",query=query,account_ref=account_ref,marketplace=marketplace
            ))
            return APIResponse(status_code=200,data={
                "state":"verified",
                "provider":"amazon",
                "account_ref":account_ref,
                "affiliate_url":link.affiliate_url,
                "product_ref":link.product_ref,
                "source":link.source,
                "evidence":dict(link.evidence),
            })
        except RuntimeError as exc:
            return APIResponse(status_code=409,error=str(exc))
        except (TypeError,ValueError) as exc:
            return APIResponse(status_code=400,error=str(exc))
        except Exception as exc:
            logger.exception("Amazon browser affiliate search failed")
            return APIResponse(status_code=502,error=str(exc))

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
        started = time.monotonic()
        platform = params.get("platform", [None])[0]
        try:
            from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
            registry=AccountRegistry(); enabled=params.get("enabled",["true"])[0].lower()!="false"
            accounts=registry.list(platform=platform,enabled_only=enabled)
            logger.info("Account lookup succeeded platform=%s count=%d elapsed_ms=%d", platform or "all", len(accounts), int((time.monotonic()-started)*1000))
            return APIResponse(data={"accounts":[a.__dict__ for a in accounts],"count":len(accounts)})
        except Exception as exc:
            logger.exception("Account lookup failed platform=%s elapsed_ms=%d", platform or "all", int((time.monotonic()-started)*1000))
            return APIResponse(500,error=str(exc))
    def _handle_account_create(self,data):
        try:
            from dataclasses import asdict
            from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry, AccountSpec
            required=("account_id","platform","niche")
            missing=[key for key in required if not str(data.get(key,"")).strip()]
            if missing: return APIResponse(400,error=f"missing required fields: {', '.join(missing)}")
            spec=AccountSpec(account_id=str(data["account_id"]),platform=str(data["platform"]),niche=str(data["niche"]),display_name=str(data.get("display_name", "")),audience=str(data.get("audience", "")),credentials_ref=str(data.get("credentials_ref", "")),affiliate_rules=dict(data.get("affiliate_rules") or {}),capabilities=list(data.get("capabilities") or []),constraints=dict(data.get("constraints") or {}),enabled=bool(data.get("enabled",True)),tenant_id=str(data.get("tenant_id", "")),workspace_id=str(data.get("workspace_id", "")),brand_id=str(data.get("brand_id", "")),platform_account_id=str(data.get("platform_account_id", "")),external_account_id=str(data.get("external_account_id", "")),tenant_name=str(data.get("tenant_name", "")),workspace_name=str(data.get("workspace_name", "")),brand_name=str(data.get("brand_name", "")),platform_account_name=str(data.get("platform_account_name", "")))
            workspace=AccountRegistry().register(spec)
            return APIResponse(status_code=201,data={"account":asdict(spec),"workspace":str(workspace),"provisioned_stores":["memory","content","analytics","learning"]})
        except (TypeError,ValueError) as exc: return APIResponse(400,error=str(exc))
        except Exception as exc: return APIResponse(500,error=str(exc))
    def _handle_pinterest_credential_store(self, data):
        """Store a Pinterest OAuth credential in the canonical encrypted L13 vault."""
        try:
            from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
            from layers.layer13_persistence.modules.postgresql.repositories.credential_repository import CredentialRepository

            required = ("account_id", "platform_account_id", "credential_ref", "access_token")
            missing = [k for k in required if not str(data.get(k) or "").strip()]
            if missing:
                return APIResponse(400, error=f"missing required fields: {', '.join(missing)}")

            account_id = str(data["account_id"]).strip()
            platform_account_id = str(data["platform_account_id"]).strip()
            credential_ref = str(data["credential_ref"]).strip()
            account = AccountRegistry().get(account_id)
            if account is None:
                return APIResponse(404, error="unknown account_id")
            if not account.enabled or account.platform != "pinterest":
                return APIResponse(409, error="account is not an enabled Pinterest account")
            if account.platform_account_id != platform_account_id:
                return APIResponse(409, error="platform_account_id does not match canonical account identity")
            if account.credentials_ref != credential_ref:
                return APIResponse(409, error="credential_ref does not match canonical account identity")

            key = os.environ.get("UCOS_CREDENTIAL_ENCRYPTION_KEY", "").strip()
            if not key:
                return APIResponse(503, error="credential encryption is not configured")

            payload = {
                "access_token": str(data["access_token"]),
                "refresh_token": str(data.get("refresh_token") or ""),
                "token_type": str(data.get("token_type") or "bearer"),
                "scope": str(data.get("scope") or ""),
                "pinterest_user_id": str(data.get("pinterest_user_id") or ""),
                "username": str(data.get("username") or ""),
                "board_id": str(data.get("board_id") or ""),
                "refresh_token_expires_at": str(data.get("refresh_token_expires_at") or ""),
            }
            expires_at = data.get("expires_at")
            credential_id = CredentialRepository(encryption_key=key).upsert(
                credential_ref=credential_ref,
                account_id=account_id,
                platform_account_id=platform_account_id,
                payload=payload,
                key_version="v1",
                expires_at=expires_at,
            )
            return APIResponse(status_code=201, data={
                "stored": True,
                "credential_id": credential_id,
                "credential_ref": credential_ref,
                "account_id": account_id,
                "platform_account_id": platform_account_id,
            })
        except (TypeError, ValueError) as exc:
            return APIResponse(400, error=str(exc))
        except Exception:
            logger.exception("Pinterest credential vault write failed")
            return APIResponse(500, error="Pinterest credential vault write failed")

    def _handle_pinterest_credential_revoke(self, data):
        """Revoke a Pinterest credential without returning or exposing its secret."""
        try:
            from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
            from layers.layer13_persistence.modules.postgresql.repositories.credential_repository import CredentialRepository
            account_id = str(data.get("account_id") or "").strip()
            credential_ref = str(data.get("credential_ref") or "").strip()
            if not account_id or not credential_ref:
                return APIResponse(400, error="account_id and credential_ref are required")
            account = AccountRegistry().get(account_id)
            if account is None:
                return APIResponse(404, error="unknown account_id")
            if account.credentials_ref != credential_ref or account.platform != "pinterest":
                return APIResponse(409, error="credential identity mismatch")
            key = os.environ.get("UCOS_CREDENTIAL_ENCRYPTION_KEY", "").strip()
            if not key:
                return APIResponse(503, error="credential encryption is not configured")
            revoked = CredentialRepository(encryption_key=key).revoke(credential_ref, account_id)
            return APIResponse(data={"revoked": bool(revoked), "account_id": account_id, "credential_ref": credential_ref})
        except Exception:
            logger.exception("Pinterest credential revoke failed")
            return APIResponse(500, error="Pinterest credential revoke failed")

    def _refresh_pinterest_token_if_needed(self, account, credentials, client_id, client_secret):
        """Refresh a Pinterest access token shortly before expiry and rotate it in L13."""
        expires_raw = str(credentials.get("expires_at") or "").strip()
        if not expires_raw:
            # Legacy credentials without expiry metadata remain usable, but cannot
            # be proactively refreshed until a new OAuth grant records the expiry.
            return credentials
        try:
            expiry = datetime.fromisoformat(expires_raw.replace("Z", "+00:00"))
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
        except ValueError:
            raise PinterestCredentialRefreshError("Pinterest credential expiry metadata is invalid")

        if expiry.timestamp() > time.time() + 300:
            return credentials

        refresh_token = str(credentials.get("refresh_token") or "").strip()
        client_id = str(client_id or "").strip()
        client_secret = str(client_secret or "").strip()
        if not refresh_token:
            raise PinterestCredentialRefreshError("Pinterest refresh token is missing; reconnect Pinterest")
        if not client_id or not client_secret:
            raise PinterestCredentialRefreshError("Pinterest token refresh is not configured")

        form = urlencode({"grant_type": "refresh_token", "refresh_token": refresh_token})
        basic = b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
        request = Request(
            "https://api.pinterest.com/v5/oauth/token",
            data=form.encode("utf-8"),
            method="POST",
            headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urlopen(request, timeout=20) as response:
                raw = response.read(1_000_000)
                token_data = json.loads(raw.decode("utf-8")) if raw else {}
        except HTTPError as exc:
            # Never include provider response bodies in logs or client responses;
            # they may contain sensitive diagnostics.
            logger.warning("Pinterest token refresh rejected status=%s account_id=%s", exc.code, account.account_id)
            raise PinterestCredentialRefreshError("Pinterest token refresh failed; reconnect Pinterest if it persists")
        except (URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.warning("Pinterest token refresh unavailable account_id=%s cause=%s", account.account_id, type(exc).__name__)
            raise PinterestCredentialRefreshError("Pinterest token refresh is temporarily unavailable")

        new_access = str(token_data.get("access_token") or "").strip()
        if not new_access:
            raise PinterestCredentialRefreshError("Pinterest did not return a refreshed access token")
        try:
            expires_in = max(1, int(token_data.get("expires_in") or 2592000))
        except (TypeError, ValueError):
            expires_in = 2592000
        new_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        rotated_refresh = str(token_data.get("refresh_token") or refresh_token)
        refresh_expiry = credentials.get("refresh_token_expires_at") or ""
        if token_data.get("refresh_token_expires_at"):
            try:
                refresh_expiry = datetime.fromtimestamp(float(token_data["refresh_token_expires_at"]), timezone.utc).isoformat()
            except (TypeError, ValueError, OverflowError):
                pass
        elif token_data.get("refresh_token_expires_in"):
            try:
                refresh_expiry = (datetime.now(timezone.utc) + timedelta(seconds=int(token_data["refresh_token_expires_in"]))).isoformat()
            except (TypeError, ValueError, OverflowError):
                pass

        payload = {
            "access_token": new_access,
            "refresh_token": rotated_refresh,
            "token_type": str(token_data.get("token_type") or credentials.get("token_type") or "bearer"),
            "scope": str(token_data.get("scope") or credentials.get("scope") or ""),
            "pinterest_user_id": str(credentials.get("pinterest_user_id") or ""),
            "username": str(credentials.get("username") or ""),
            "board_id": str(credentials.get("board_id") or ""),
            "refresh_token_expires_at": str(refresh_expiry),
        }
        from layers.layer13_persistence.modules.postgresql.repositories.credential_repository import CredentialRepository
        key = os.environ.get("UCOS_CREDENTIAL_ENCRYPTION_KEY", "").strip()
        if not key:
            raise PinterestCredentialRefreshError("Credential encryption is not configured")
        CredentialRepository(encryption_key=key).upsert(
            credential_ref=account.credentials_ref,
            account_id=account.account_id,
            platform_account_id=account.platform_account_id,
            payload=payload,
            key_version=str(credentials.get("key_version") or "v1"),
            expires_at=new_expiry,
        )
        payload["expires_at"] = new_expiry.isoformat()
        return payload

    def _handle_pinterest_operation(self, data):
        """Execute a safe Pinterest operation without exposing the stored OAuth token."""
        try:
            from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
            from layers.layer17_security.modules.credential_resolver.credential_resolver import AccountCredentialResolver
            from urllib.request import Request, urlopen
            import urllib.error

            account_id = str(data.get("account_id") or "").strip()
            operation = str(data.get("operation") or "").strip().lower()
            if not account_id or not operation:
                return APIResponse(400, error="account_id and operation are required")

            account = AccountRegistry().get(account_id)
            if account is None:
                return APIResponse(404, error="unknown account_id")
            if not account.enabled or account.platform != "pinterest":
                return APIResponse(409, error="account is not an enabled Pinterest account")

            credentials = AccountCredentialResolver.resolve(account.credentials_ref, account_id)
            credentials = self._refresh_pinterest_token_if_needed(
                account,
                credentials,
                data.get("pinterest_client_id"),
                data.get("pinterest_client_secret"),
            )
            token = str(credentials.get("access_token") or "").strip()
            if not token:
                return APIResponse(401, error="Pinterest credential is not configured")

            base = "https://api.pinterest.com/v5"
            method = "GET"
            path = "/user_account"
            body = None
            payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}

            if operation == "account":
                method, path = "GET", "/user_account"
            elif operation == "boards":
                method, path = "GET", "/boards"
            elif operation == "create_board":
                name = str(payload.get("name") or "").strip()
                if not name:
                    return APIResponse(400, error="board name is required")
                method, path = "POST", "/boards"
                body = {"name": name, "description": str(payload.get("description") or "")}
            elif operation == "create_pin":
                required = ("board_id", "title", "image_url")
                missing = [k for k in required if not str(payload.get(k) or "").strip()]
                if missing:
                    return APIResponse(400, error=f"missing required fields: {', '.join(missing)}")
                method, path = "POST", "/pins"
                body = {
                    "board_id": str(payload["board_id"]),
                    "title": str(payload["title"]),
                    "description": str(payload.get("description") or ""),
                    "media_source": {
                        "source_type": "image_url",
                        "url": str(payload["image_url"]),
                        "is_standard": True,
                    },
                }
                if str(payload.get("destination_url") or "").strip():
                    body["link"] = str(payload["destination_url"])
            else:
                return APIResponse(400, error="unsupported Pinterest operation")

            encoded = json.dumps(body).encode("utf-8") if body is not None else None
            request = Request(
                f"{base}{path}",
                data=encoded,
                method=method,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            try:
                with urlopen(request, timeout=30) as response:
                    raw = response.read(2_000_000)
                    result = json.loads(raw.decode("utf-8")) if raw else {}
                    return APIResponse(status_code=response.status, data=result)
            except urllib.error.HTTPError as exc:
                raw = exc.read(2_000_000)
                try:
                    detail = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    detail = {}
                return APIResponse(status_code=exc.code, error=str(
                    detail.get("message") or detail.get("error_description") or detail.get("error") or
                    f"Pinterest HTTP {exc.code}"
                ))
            except (urllib.error.URLError, TimeoutError) as exc:
                return APIResponse(502, error=f"Pinterest API unavailable: {type(exc).__name__}")
        except PinterestCredentialRefreshError as exc:
            return APIResponse(503 if "temporarily unavailable" in str(exc) else 401, error=str(exc))
        except Exception:
            logger.exception("Pinterest operation failed")
            return APIResponse(500, error="Pinterest operation failed")

    def _handle_pinterest_credentials(self, params):
        """Return non-secret Pinterest credential metadata only."""
        try:
            from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
            account_id = str(params.get("account_id", [""])[0] or "").strip()
            if not account_id:
                return APIResponse(400, error="account_id is required")
            account = AccountRegistry().get(account_id)
            if account is None:
                return APIResponse(404, error="unknown account_id")
            if account.platform != "pinterest":
                return APIResponse(409, error="account is not a Pinterest account")
            return APIResponse(data={
                "account_id": account.account_id,
                "platform": account.platform,
                "platform_account_id": account.platform_account_id,
                "credential_ref": account.credentials_ref,
                "enabled": account.enabled,
            })
        except Exception:
            logger.exception("Pinterest credential metadata lookup failed")
            return APIResponse(500, error="Pinterest credential metadata lookup failed")

    def _handle_generate(self,data):
        topic=data.get("topic","artificial intelligence"); platform=data.get("platform"); account_id=data.get("account_id"); tone=data.get("tone","professional"); style=data.get("style","educational"); include_image=bool(data.get("include_image",True)); publish_mode=data.get("publish_mode")
        try:
            from layers.layer14_enterprise_integration.modules.master_orchestrator.control_plane import ControlPlane
            result=ControlPlane().execute(topic=topic,platform=platform,account_id=account_id,tone=tone,style=style,include_image=include_image,publish_mode=publish_mode)
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
