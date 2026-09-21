"""InstagramPublisher — Real Instagram Graph API integration."""
from __future__ import annotations
import json
import time
import urllib.parse
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional
from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import BasePublisher, PublishResult, PlatformCapabilities

class InstagramPublisher(BasePublisher):
    API_BASE = f"https://graph.facebook.com/{__import__('os').environ.get('META_GRAPH_API_VERSION', 'v26.0')}"

    def __init__(self) -> None:
        self._account_id: str = ""
        self._access_token: str = ""
        self._authenticated: bool = False
        self._request_count: int = 0
        self._success_count: int = 0
        self._error_count: int = 0
        self._history: List[Dict[str, Any]] = []

    def get_platform_name(self) -> str: return "instagram"

    def get_capabilities(self) -> PlatformCapabilities:
        caps = PlatformCapabilities(); caps.supports_images=True; caps.supports_video=True; caps.supports_carousel=True; caps.supports_scheduled=False; caps.supports_edit=False; caps.supports_delete=True; caps.supports_analytics=True; caps.supports_threads=False; caps.supports_stories=True; caps.supports_polls=False; caps.max_length=2200; caps.max_images=10; caps.features=["feed","stories","reels","carousel","insights"]; return caps

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        self._account_id=credentials.get("account_id", ""); self._access_token=credentials.get("access_token", ""); self._authenticated=False
        if not self._account_id or not self._access_token: return False
        try:
            result=self._api_get(f"/{self._account_id}", {"fields":"id,username"})
            self._authenticated=bool(result and result.get("id")==self._account_id)
        except Exception: self._authenticated=False
        return self._authenticated

    def validate(self, content: str, content_type: str = "post") -> bool:
        return bool(content and content.strip() and len(content)<=self.get_capabilities().max_length)

    def publish(self, content: str, media_paths: Optional[List[str]]=None, content_type: str="post", **kwargs: Any) -> PublishResult:
        result=PublishResult(platform="instagram"); start=time.time()
        if not self._authenticated: result.error_message="Not authenticated"; return result
        if not self.validate(content,content_type): result.error_message="Content validation failed"; return result
        try:
            if content_type=="story": api_result=self._publish_story(content,media_paths,**kwargs)
            elif content_type=="reel": api_result=self._publish_reel(content,media_paths,**kwargs)
            elif media_paths and len(media_paths)>1: api_result=self._publish_carousel(content,media_paths,**kwargs)
            else: api_result=self._publish_feed(content,media_paths,**kwargs)
            if api_result and "id" in api_result:
                result.success=True; result.post_id=api_result["id"]; result.url=f"https://instagram.com/p/{api_result['id']}"; result.metadata={"platform":"instagram","content_type":content_type,"account_id":self._account_id}; self._success_count+=1
            else: result.error_message=str(api_result.get("error","Unknown")) if api_result else "No response"; self._error_count+=1
        except Exception as exc: result.error_message=str(exc); self._error_count+=1
        self._request_count+=1; self._history.append({"action":"publish","success":result.success,"post_id":result.post_id,"latency_ms":round((time.time()-start)*1000,1),"time":time.time()}); return result

    def edit(self, post_id: str, content: str, **kwargs: Any) -> PublishResult:
        r=PublishResult(platform="instagram"); r.error_message="Instagram API does not support post editing"; return r
    def delete(self, post_id: str) -> bool:
        try: return self._api_delete(f"/{post_id}") is not None
        except Exception: return False
    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        try: return self._api_get(f"/{post_id}", {"fields":"id,caption,media_type,timestamp,like_count,comments_count"})
        except Exception: return None
    def get_status(self, post_id: str) -> str: return "published" if self.get_post(post_id) else "unknown"
    def get_analytics(self, post_id: str) -> Dict[str, Any]:
        try:
            post=self._api_get(f"/{post_id}", {"fields":"like_count,comments_count,insights.metric(impressions,reach,engagement)"})
            if not post: return {"post_id":post_id,"analytics":"UNKNOWN"}
            insights=post.get("insights",{}).get("data",[]); metrics={i["name"]:i["values"][0]["value"] for i in insights if i.get("values")}
            return {"post_id":post_id,"likes":post.get("like_count",0),"comments":post.get("comments_count",0),"impressions":metrics.get("impressions","UNKNOWN"),"reach":metrics.get("reach","UNKNOWN"),"engagement":metrics.get("engagement","UNKNOWN")}
        except Exception: return {"post_id":post_id,"analytics":"UNKNOWN"}
    def schedule(self, content: str, scheduled_time: float, media_paths: Optional[List[str]]=None, **kwargs: Any) -> PublishResult:
        r=PublishResult(platform="instagram"); r.error_message="Instagram API does not support scheduling via Graph API"; return r
    def get_account_info(self) -> Dict[str, Any]:
        try: return self._api_get(f"/{self._account_id}", {"fields":"id,username,name,biography,followers_count,media_count"}) or {}
        except Exception: return {}
    def get_stats(self) -> Dict[str, Any]: return {"platform":"instagram","authenticated":self._authenticated,"account_id":self._account_id,"total_requests":self._request_count,"successful":self._success_count,"errors":self._error_count}

    def _publish_feed(self, content: str, media_paths: Optional[List[str]]=None, **kwargs: Any) -> Optional[Dict]:
        if not media_paths: return {"error":"Instagram feed posts require media"}
        c=self._api_post(f"/{self._account_id}/media", {"image_url":media_paths[0],"caption":content})
        if not c or "id" not in c: return c
        self._wait_for_container(c["id"])\n        return self._api_post(f"/{self._account_id}/media_publish", {"creation_id":c["id"]})
    def _publish_carousel(self, content: str, media_paths: List[str], **kwargs: Any) -> Optional[Dict]:
        children=[]
        for url in media_paths[:10]:
            c=self._api_post(f"/{self._account_id}/media", {"image_url":url,"is_carousel_item":"true"})
            if c and "id" in c: children.append(c["id"])
        if not children: return {"error":"No valid carousel items"}
        c=self._api_post(f"/{self._account_id}/media", {"media_type":"CAROUSEL_ALBUM","caption":content,"children":",".join(children)})
        if not c or "id" not in c: return c
        self._wait_for_container(c["id"])
        return self._api_post(f"/{self._account_id}/media_publish", {"creation_id":c["id"]})
    def _publish_story(self, content: str, media_paths: Optional[List[str]]=None, **kwargs: Any) -> Optional[Dict]:
        if not media_paths: return {"error":"Stories require media"}
        c=self._api_post(f"/{self._account_id}/media", {"image_url":media_paths[0],"media_type":"STORIES"})
        if not c or "id" not in c: return c
        self._wait_for_container(c["id"])
        return self._api_post(f"/{self._account_id}/media_publish", {"creation_id":c["id"]})
    def _publish_reel(self, content: str, media_paths: Optional[List[str]]=None, **kwargs: Any) -> Optional[Dict]:
        if not media_paths: return {"error":"Reels require video URL"}
        c=self._api_post(f"/{self._account_id}/media", {"media_type":"REELS","video_url":media_paths[0],"caption":content})
        if not c or "id" not in c: return c
        self._wait_for_container(c["id"])
        return self._api_post(f"/{self._account_id}/media_publish", {"creation_id":c["id"]})
    def _wait_for_container(self, container_id: str, timeout: float = 120.0, interval: float = 3.0) -> None:
        """Wait for Meta async media processing before media_publish."""
        deadline = time.time() + timeout
        last_status = ""
        while time.time() < deadline:
            state = self._api_get(f"/{container_id}", {"fields": "status_code,status"}) or {}
            last_status = str(state.get("status_code") or state.get("status") or "").upper()
            if last_status == "FINISHED":
                return
            if last_status in {"ERROR", "EXPIRED"}:
                raise RuntimeError(f"Instagram media container {container_id} failed: {last_status}")
            time.sleep(interval)
        raise TimeoutError(f"Instagram media container {container_id} did not reach FINISHED (last={last_status or 'UNKNOWN'})")

    def _api_get(self, endpoint: str, params: Optional[Dict]=None) -> Optional[Dict]:
        url=f"{self.API_BASE}{endpoint}"; url=f"{url}?{urllib.parse.urlencode(params)}" if params else url
        try:
            with urllib.request.urlopen(urllib.request.Request(url,method="GET"),timeout=30) as resp: return json.loads(resp.read().decode("utf-8"))
        except Exception: return None
    def _api_post(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict]:
        payload=dict(data); payload["access_token"]=self._access_token
        try:
            req=urllib.request.Request(f"{self.API_BASE}{endpoint}",data=json.dumps(payload).encode("utf-8"),headers={"Content-Type":"application/json"},method="POST")
            with urllib.request.urlopen(req,timeout=30) as resp: return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try: return {"error":f"HTTP {exc.code}: {exc.read().decode('utf-8','replace')[:200]}"}
            except Exception: return {"error":f"HTTP {exc.code}"}
        except Exception: return {"error":"Network unavailable"}
    def _api_delete(self, endpoint: str) -> Optional[Dict]:
        url=f"{self.API_BASE}{endpoint}?{urllib.parse.urlencode({'access_token':self._access_token})}"
        try:
            with urllib.request.urlopen(urllib.request.Request(url,method="DELETE"),timeout=30) as resp: return json.loads(resp.read().decode("utf-8"))
        except Exception: return None
