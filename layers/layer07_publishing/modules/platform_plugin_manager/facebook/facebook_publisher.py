"""Real Facebook Page publisher using the Graph API."""
from __future__ import annotations
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional
from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import BasePublisher, PlatformCapabilities, PublishResult

class FacebookPublisher(BasePublisher):
    API_BASE = "https://graph.facebook.com/v19.0"
    def __init__(self) -> None:
        self._page_id=""; self._access_token=""; self._authenticated=False
        self._request_count=0; self._success_count=0; self._error_count=0
        self._rate_limit_remaining=200; self._rate_limit_reset=0.0
    def get_platform_name(self): return "facebook"
    def get_capabilities(self):
        c=PlatformCapabilities(); c.supports_images=True; c.supports_video=True; c.supports_scheduled=True; c.supports_edit=True; c.supports_delete=True; c.supports_analytics=True; c.supports_stories=True; c.supports_polls=True; c.max_length=63206; c.max_images=10; c.features=["pages","stories","reels","polls","events"]; return c
    def authenticate(self, credentials: Dict[str,str]) -> bool:
        # Credentials are account-scoped; never read process-wide Facebook secrets.
        self._page_id=credentials.get("page_id",""); token=credentials.get("access_token",""); self._authenticated=False
        if not self._page_id or not token: return False
        self._access_token=token
        try:
            page=self._api_get(f"/{self._page_id}",{"fields":"id,name"})
            if page.get("id")==self._page_id: self._authenticated=True; return True
        except Exception: pass
        try:
            accounts=self._api_get("/me/accounts",{"fields":"id,name,access_token"},token=token)
            for page in accounts.get("data",[]):
                if str(page.get("id"))==str(self._page_id) and page.get("access_token"):
                    self._access_token=page["access_token"]; validated=self._api_get(f"/{self._page_id}",{"fields":"id,name"}); self._authenticated=validated.get("id")==self._page_id; return self._authenticated
        except Exception: pass
        return False
    def validate(self,content,content_type="post"): return bool(content and content.strip()) and len(content)<=self.get_capabilities().max_length
    def publish(self,content,media_paths=None,content_type="post",**kwargs):
        r=PublishResult(platform="facebook")
        if not self._authenticated: r.error_message="Not authenticated"; return r
        if not self.validate(content,content_type): r.error_message="Content validation failed"; return r
        if self._rate_limit_remaining<=0 and time.time()<self._rate_limit_reset: r.error_message="Rate limited"; return r
        try:
            if media_paths and content_type in ("photo","image"): payload=self._publish_with_media(content,media_paths,**kwargs)
            elif kwargs.get("link"): payload=self._post(f"/{self._page_id}/feed",{"message":content,"link":kwargs["link"]})
            else: payload=self._post(f"/{self._page_id}/feed",{"message":content})
            if payload.get("id"): r.success=True; r.post_id=str(payload["id"]); r.url=f"https://facebook.com/{payload['id']}"; self._success_count+=1
            else: r.error_message=str(payload.get("error","Unknown")); self._error_count+=1
        except Exception as e: r.error_message=str(e); self._error_count+=1
        self._request_count+=1; return r
    def edit(self,post_id,content,**kwargs):
        r=PublishResult(platform="facebook")
        try: data=self._post(f"/{post_id}",{"message":content}); r.success=bool(data and not data.get("error")); r.post_id=post_id; r.url=f"https://facebook.com/{post_id}"
        except Exception as e: r.error_message=str(e)
        return r
    def delete(self,post_id):
        try: return bool(self._api_delete(f"/{post_id}"))
        except Exception: return False
    def get_post(self,post_id):
        try: return self._api_get(f"/{post_id}",{"fields":"id,message,created_time,permalink_url"})
        except Exception: return None
    def get_status(self,post_id): return "published" if self.get_post(post_id) else "unknown"
    def get_analytics(self,post_id):
        try:
            data=self._api_get(f"/{post_id}/insights",{"metric":"post_impressions,post_reactions_by_type_total,post_comments"})
            return {"post_id":post_id,"metrics":data.get("data",[])} if data else {"post_id":post_id,"analytics":"UNKNOWN"}
        except Exception: return {"post_id":post_id,"analytics":"UNKNOWN"}
    def schedule(self,content,scheduled_time,media_paths=None,**kwargs):
        r=PublishResult(platform="facebook")
        if not self._authenticated: r.error_message="Not authenticated"; return r
        payload={"message":content,"published":"false","scheduled_publish_time":int(scheduled_time)}
        try:
            data=self._post(f"/{self._page_id}/feed",payload); pid=data.get("id") if data else None
            if pid: r.success=True; r.post_id=str(pid); r.metadata={"scheduled":True}
            else: r.error_message=str(data or "Facebook returned no post id")
        except Exception as e: r.error_message=str(e)
        return r
    def get_stats(self): return {"platform":"facebook","authenticated":self._authenticated,"page_id":self._page_id,"total_requests":self._request_count,"successful":self._success_count,"errors":self._error_count}
    def _publish_with_media(self,content,media_paths,**kwargs): return self._post(f"/{self._page_id}/photos",{"url":media_paths[0],"caption":content})
    def _api_get(self,endpoint,params=None,token=None):
        p=dict(params or {}); p["access_token"]=token or self._access_token; url=f"{self.API_BASE}{endpoint}?{urllib.parse.urlencode(p)}"
        req=urllib.request.Request(url,method="GET")
        with urllib.request.urlopen(req,timeout=30) as resp: return json.loads(resp.read().decode())
    def _post(self,endpoint,data):
        p=dict(data); p["access_token"]=self._access_token; url=f"{self.API_BASE}{endpoint}"
        req=urllib.request.Request(url,data=urllib.parse.urlencode(p).encode(),headers={"Content-Type":"application/x-www-form-urlencoded"},method="POST")
        with urllib.request.urlopen(req,timeout=60) as resp: return json.loads(resp.read().decode())
    def _api_delete(self,endpoint):
        url=f"{self.API_BASE}{endpoint}?{urllib.parse.urlencode({'access_token':self._access_token})}"; req=urllib.request.Request(url,method="DELETE")
        with urllib.request.urlopen(req,timeout=30) as resp: return json.loads(resp.read().decode())
