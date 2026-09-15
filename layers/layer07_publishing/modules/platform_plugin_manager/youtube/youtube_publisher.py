"""YouTube Data API v3 publisher using OAuth bearer tokens and resumable uploads."""
from __future__ import annotations
import json, mimetypes, os, urllib.parse, urllib.request, urllib.error
from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import BasePublisher, PublishResult, PlatformCapabilities

class YouTubePublisher(BasePublisher):
    UPLOAD="https://www.googleapis.com/upload/youtube/v3/videos"; API="https://www.googleapis.com/youtube/v3"
    def __init__(self): self.token=""; self.authenticated=False
    def get_platform_name(self): return "youtube"
    def get_capabilities(self):
        c=PlatformCapabilities(); c.supports_video=True; c.supports_analytics=True; c.supports_edit=True; c.supports_delete=True; c.max_length=5000; c.features=["video_upload","video_metadata","statistics"]; return c
    def authenticate(self, credentials):
        # Credentials are account-scoped. Never fall back to process-wide environment state.
        self.token=credentials.get("access_token", "")
        self.authenticated=False
        if not self.token: return False
        try: self.authenticated=bool(self._get("/channels",{"part":"id","mine":"true"}).get("items"))
        except Exception: self.authenticated=False
        return self.authenticated
    def validate(self, content, content_type="video"): return bool(content and len(content)<=5000)
    def publish(self, content, media_paths=None, content_type="video", **kwargs):
        r=PublishResult(platform="youtube")
        if not self.authenticated: r.error_message="Not authenticated"; return r
        if not media_paths or not os.path.isfile(media_paths[0]): r.error_message="YouTube publishing requires a local video file"; return r
        try:
            title=kwargs.get("title") or content.splitlines()[0][:100] or "UCOS video"
            result=self._upload(media_paths[0],{"snippet":{"title":title,"description":content},"status":{"privacyStatus":kwargs.get("privacy_status","private")}})
            vid=result.get("id") if result else None
            if vid: r.success=True; r.post_id=vid; r.url=f"https://www.youtube.com/watch?v={vid}"
            else: r.error_message=str(result or "YouTube returned no video id")
        except Exception as e: r.error_message=str(e)
        return r
    def edit(self, post_id, content, **kwargs):
        r=PublishResult(platform="youtube")
        try:
            body={"id":post_id,"snippet":{"title":kwargs.get("title",content[:100]),"description":content,"categoryId":kwargs.get("category_id","22")}}
            data=self._request("PUT","/videos",{"part":"snippet"},body); r.success=bool(data and data.get("id")); r.post_id=post_id; r.url=f"https://www.youtube.com/watch?v={post_id}"; r.error_message="" if r.success else str(data)
        except Exception as e: r.error_message=str(e)
        return r
    def delete(self, post_id):
        try: self._request("DELETE","/videos",{"id":post_id},None); return True
        except Exception: return False
    def get_post(self, post_id):
        try: return self._get("/videos",{"part":"snippet,statistics,status","id":post_id})
        except Exception: return None
    def get_status(self, post_id): return "published" if self.get_post(post_id) else "unknown"
    def get_analytics(self, post_id):
        try:
            data=self._get("/videos",{"part":"statistics","id":post_id}); items=data.get("items",[]) if data else []
            return items[0].get("statistics",{}) if items else {"post_id":post_id,"analytics":"UNKNOWN"}
        except Exception: return {"post_id":post_id,"analytics":"UNKNOWN"}
    def schedule(self, content, scheduled_time, media_paths=None, **kwargs):
        r=PublishResult(platform="youtube"); r.error_message="Scheduling requires an explicitly configured publishAt workflow"; return r
    def _upload(self,path,body):
        size=os.path.getsize(path); mime=mimetypes.guess_type(path)[0] or "video/mp4"
        req=urllib.request.Request(self.UPLOAD+"?uploadType=resumable&part=snippet,status",data=json.dumps(body).encode(),method="POST",headers={"Authorization":f"Bearer {self.token}","Content-Type":"application/json; charset=UTF-8","X-Upload-Content-Type":mime,"X-Upload-Content-Length":str(size)})
        with urllib.request.urlopen(req,timeout=30) as resp: location=resp.headers.get("Location")
        if not location: raise RuntimeError("YouTube did not return resumable upload URL")
        with open(path,"rb") as f: data=f.read()
        req2=urllib.request.Request(location,data=data,method="PUT",headers={"Authorization":f"Bearer {self.token}","Content-Type":mime,"Content-Length":str(size)})
        with urllib.request.urlopen(req2,timeout=300) as resp: return json.loads(resp.read().decode())
    def _get(self,path,params): return self._request("GET",path,params,None)
    def _request(self,method,path,params,body):
        q=urllib.parse.urlencode(params or {}); url=self.API+path+("?"+q if q else "")
        req=urllib.request.Request(url,data=json.dumps(body).encode() if body is not None else None,method=method,headers={"Authorization":f"Bearer {self.token}","Content-Type":"application/json"})
        try:
            with urllib.request.urlopen(req,timeout=60) as resp: return json.loads(resp.read().decode()) if resp.readable() else {}
        except urllib.error.HTTPError as e: raise RuntimeError(f"YouTube HTTP {e.code}: {e.read().decode('utf-8','replace')[:1000]})
