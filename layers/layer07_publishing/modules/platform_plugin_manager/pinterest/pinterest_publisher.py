"""Pinterest API v5 publisher.

Requires an OAuth access token with pins:write/pins:read and a board_id.
Media must be a publicly reachable HTTPS image URL for image Pins.
"""
from __future__ import annotations
import json, os, time, urllib.parse, urllib.request, urllib.error
from typing import Any, Dict, List, Optional
from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import BasePublisher, PublishResult, PlatformCapabilities

class PinterestPublisher(BasePublisher):
    API_BASE = "https://api.pinterest.com/v5"
    def __init__(self):
        self.token=""; self.board_id=""; self.authenticated=False
    def get_platform_name(self): return "pinterest"
    def get_capabilities(self):
        c=PlatformCapabilities(); c.supports_images=True; c.supports_video=True; c.supports_delete=True; c.supports_analytics=True; c.max_length=500; c.features=["pins","boards","analytics"]; return c
    def authenticate(self, credentials):
        self.token=credentials.get("access_token") or os.getenv("PINTEREST_ACCESS_TOKEN","")
        self.board_id=credentials.get("board_id") or os.getenv("PINTEREST_BOARD_ID","")
        if not self.token or not self.board_id: return False
        try:
            r=self._request("GET", "/user_account", None)
            self.authenticated=bool(r and r.get("username"))
        except Exception: self.authenticated=False
        return self.authenticated
    def validate(self, content, content_type="post"):
        return bool(content and len(content)<=500 and self.board_id)
    def publish(self, content, media_paths=None, content_type="post", **kwargs):
        r=PublishResult(platform="pinterest")
        if not self.authenticated: r.error_message="Not authenticated"; return r
        if not self.validate(content): r.error_message="Pinterest validation failed"; return r
        url=(media_paths or [""])[0]
        if not url.startswith("http://") and not url.startswith("https://"):
            r.error_message="Pinterest image/video Pins require a publicly reachable media URL"; return r
        body={"board_id":self.board_id,"title":kwargs.get("title",content[:100]),"description":content,"media_source":{"source_type":"image_url","url":url}}
        if kwargs.get("link"): body["link"]=kwargs["link"]
        try:
            data=self._request("POST","/pins",body)
            if data and data.get("id"):
                r.success=True; r.post_id=str(data["id"]); r.url=f"https://www.pinterest.com/pin/{data['id']}/"; r.metadata={"board_id":self.board_id}
            else: r.error_message=str(data or "Pinterest returned no pin id")
        except Exception as e: r.error_message=str(e)
        return r
    def edit(self, post_id, content, **kwargs):
        r=PublishResult(platform="pinterest")
        try:
            data=self._request("PATCH",f"/pins/{post_id}",{"description":content})
            r.success=bool(data and data.get("id")); r.post_id=str(post_id); r.url=f"https://www.pinterest.com/pin/{post_id}/"; r.error_message="" if r.success else str(data)
        except Exception as e: r.error_message=str(e)
        return r
    def delete(self, post_id):
        try: self._request("DELETE",f"/pins/{post_id}",None); return True
        except Exception: return False
    def get_post(self, post_id):
        try: return self._request("GET",f"/pins/{post_id}",None)
        except Exception: return None
    def get_status(self, post_id): return "published" if self.get_post(post_id) else "unknown"
    def get_analytics(self, post_id):
        # Organic Pin analytics require the Pinterest analytics endpoints and the
        # corresponding account scopes. Never synthesize values when unavailable.
        try: return self._request("GET",f"/pins/{post_id}",None) or {"post_id":post_id,"analytics":"UNKNOWN"}
        except Exception: return {"post_id":post_id,"analytics":"UNKNOWN"}
    def schedule(self, content, scheduled_time, media_paths=None, **kwargs):
        r=PublishResult(platform="pinterest"); r.error_message="Pinterest API publisher does not claim native scheduling"; return r
    def _request(self, method, path, body):
        url=self.API_BASE+path
        data=json.dumps(body).encode() if body is not None else None
        req=urllib.request.Request(url,data=data,method=method,headers={"Authorization":f"Bearer {self.token}","Content-Type":"application/json"})
        try:
            with urllib.request.urlopen(req,timeout=30) as resp: return json.loads(resp.read().decode()) if resp.readable() else {}
        except urllib.error.HTTPError as e:
            detail=e.read().decode("utf-8","replace")[:1000]; raise RuntimeError(f"Pinterest HTTP {e.code}: {detail}")
