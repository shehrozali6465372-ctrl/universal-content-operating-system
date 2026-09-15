"""TikTok Content Posting API Direct Post publisher.

Supports video and photo URLs. The Direct Post API returns a publish_id for
asynchronous processing; it is never reported as a final post ID.
"""
from __future__ import annotations
import json, os, urllib.request, urllib.error
from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import BasePublisher, PublishResult, PlatformCapabilities

class TikTokPublisher(BasePublisher):
    API="https://open.tiktokapis.com/v2"
    def __init__(self): self.token=""; self.authenticated=False; self.privacy="PUBLIC_TO_EVERYONE"
    def get_platform_name(self): return "tiktok"
    def get_capabilities(self):
        c=PlatformCapabilities(); c.supports_video=True; c.supports_images=True; c.supports_analytics=False; c.max_length=2200; c.features=["direct_post","photo_post","video_post","async_status"]
        return c
    def authenticate(self, credentials):
        self.token=credentials.get("access_token") or ""
        if not self.token: return False
        try:
            data=self._post("/post/publish/creator_info/query/",{})
            options=(data.get("data") or {}).get("privacy_level_options") or []
            self.privacy="PUBLIC_TO_EVERYONE" if "PUBLIC_TO_EVERYONE" in options else (options[0] if options else "SELF_ONLY")
            self.authenticated=bool(data.get("data"))
        except Exception: self.authenticated=False
        return self.authenticated
    def validate(self, content, content_type="video"): return bool(content and len(content)<=2200)
    def publish(self, content, media_paths=None, content_type="video", **kwargs):
        r=PublishResult(platform="tiktok")
        if not self.authenticated: r.error_message="Not authenticated"; return r
        if not media_paths: r.error_message="TikTok requires a public media URL"; return r
        media=media_paths[0]
        if not media.startswith(("http://","https://")): r.error_message="TikTok Direct Post requires a verified/public media URL for PULL_FROM_URL"; return r
        try:
            if content_type in ("photo","image","post"):
                body={"post_info":{"title":content[:90],"description":content,"privacy_level":self.privacy,"disable_comment":False},"source_info":{"source":"PULL_FROM_URL","photo_images":[media]},"post_mode":"DIRECT_POST","media_type":"PHOTO"}
                data=self._post("/post/publish/content/init/",body)
            else:
                body={"post_info":{"title":content[:2200],"privacy_level":self.privacy,"disable_comment":False,"is_aigc":bool(kwargs.get("is_aigc",False))},"source_info":{"source":"PULL_FROM_URL","video_url":media}}
                data=self._post("/post/publish/video/init/",body)
            pid=(data.get("data") or {}).get("publish_id")
            if pid:
                # publish_id is only an asynchronous tracking identifier. Do not
                # claim success, a public URL, or a final TikTok post ID here.
                r.success=False
                r.post_id=""
                r.url=""
                r.error_message="TikTok accepted the publish request; final publication is pending status confirmation"
                r.metadata={"publish_state":"processing","tracking_id":pid,"privacy_level":self.privacy}
            else: r.error_message=str(data)
        except Exception as e: r.error_message=str(e)
        return r
    def edit(self, post_id, content, **kwargs):
        r=PublishResult(platform="tiktok"); r.error_message="TikTok Content Posting API does not provide post editing through this interface"; return r
    def delete(self, post_id): return False
    def get_post(self, post_id):
        try: return self._post("/post/publish/status/fetch/",{"publish_id":post_id})
        except Exception: return None
    def get_status(self, post_id):
        data=self.get_post(post_id) or {}; return str((data.get("data") or {}).get("status","unknown"))
    def get_analytics(self, post_id): return {"post_id":post_id,"analytics":"UNKNOWN","reason":"Content Posting API status is not analytics"}
    def schedule(self, content, scheduled_time, media_paths=None, **kwargs):
        r=PublishResult(platform="tiktok"); r.error_message="TikTok Direct Post does not claim native scheduling here"; return r
    def _post(self,path,body):
        req=urllib.request.Request(self.API+path,data=json.dumps(body).encode(),method="POST",headers={"Authorization":f"Bearer {self.token}","Content-Type":"application/json; charset=UTF-8"})
        try:
            with urllib.request.urlopen(req,timeout=60) as resp: return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e: raise RuntimeError(f"TikTok HTTP {e.code}: {e.read().decode('utf-8','replace')[:1000]}")
