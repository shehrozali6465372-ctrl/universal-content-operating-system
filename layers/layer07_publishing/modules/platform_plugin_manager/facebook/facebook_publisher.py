"""Real Facebook Page publisher using the Graph API.

Authentication never performs a test publication. A token is validated with
read-only Graph API calls and a user token is converted to a page token through
/me/accounts when necessary.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import BasePublisher, PlatformCapabilities, PublishResult


class FacebookPublisher(BasePublisher):
    API_BASE = f"https://graph.facebook.com/{os.environ.get('META_GRAPH_API_VERSION', 'v26.0')}"

    def __init__(self) -> None:
        self._page_id = ""
        self._access_token = ""
        self._authenticated = False
        self._request_count = 0
        self._success_count = 0
        self._error_count = 0
        self._rate_limit_remaining = 200
        self._rate_limit_reset = 0.0

    def get_platform_name(self) -> str:
        return "facebook"

    def get_capabilities(self) -> PlatformCapabilities:
        caps = PlatformCapabilities()
        caps.supports_images = True; caps.supports_video = True; caps.supports_scheduled = True
        caps.supports_edit = True; caps.supports_delete = True; caps.supports_analytics = True
        caps.supports_stories = True; caps.supports_polls = True; caps.max_length = 63206
        caps.max_images = 10; caps.features = ["pages", "stories", "reels", "polls", "events"]
        return caps

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        # Account-scoped only: never read FACEBOOK_* process-wide credentials.
        self._page_id = credentials.get("page_id", "")
        token = credentials.get("access_token", "")
        self._authenticated = False
        if not self._page_id or not token:
            return False
        self._access_token = token
        try:
            page = self._api_get(f"/{self._page_id}", {"fields": "id,name"})
            if page.get("id") == self._page_id:
                self._authenticated = True
                return True
        except Exception:
            pass
        try:
            accounts = self._api_get("/me/accounts", {"fields": "id,name,access_token"}, token=token)
            for page in accounts.get("data", []):
                if str(page.get("id")) == str(self._page_id) and page.get("access_token"):
                    self._access_token = page["access_token"]
                    validated = self._api_get(f"/{self._page_id}", {"fields": "id,name"})
                    self._authenticated = validated.get("id") == self._page_id
                    return self._authenticated
        except Exception:
            pass
        return False

    def validate(self, content: str, content_type: str = "post") -> bool:
        return bool(content and content.strip()) and len(content) <= self.get_capabilities().max_length

    def publish(self, content: str, media_paths: Optional[List[str]] = None, content_type: str = "post", **kwargs: Any) -> PublishResult:
        result = PublishResult(platform="facebook")
        if not self._authenticated:
            result.error_message = "Not authenticated"; return result
        if not self.validate(content, content_type):
            result.error_message = "Content validation failed"; return result
        if self._rate_limit_remaining <= 0 and time.time() < self._rate_limit_reset:
            result.error_message = "Rate limited"; return result
        started = time.time()
        try:
            if media_paths and content_type in ("photo", "image"):
                payload = self._publish_with_media(content, media_paths, **kwargs)
            elif kwargs.get("link"):
                payload = self._post(f"/{self._page_id}/feed", {"message": content, "link": kwargs["link"]})
            else:
                payload = self._post(f"/{self._page_id}/feed", {"message": content})
            if payload.get("id"):
                result.success = True; result.post_id = str(payload["id"]); result.url = f"https://facebook.com/{result.post_id}"
                result.metadata = {"page_id": self._page_id, "content_type": content_type, "latency_ms": round((time.time()-started)*1000, 1)}
                self._success_count += 1
            else:
                result.error_message = str(payload.get("error") or payload); self._error_count += 1
        except urllib.error.HTTPError as exc:
            result.error_message = self._http_error(exc); self._error_count += 1
            if exc.code == 429:
                self._rate_limit_remaining = 0; self._rate_limit_reset = time.time() + 3600
        except Exception as exc:
            result.error_message = str(exc); self._error_count += 1
        self._request_count += 1
        return result

    def _publish_with_media(self, content: str, media_paths: List[str], **kwargs: Any) -> Dict[str, Any]:
        media_ids: List[str] = []
        for path in media_paths[:self.get_capabilities().max_images]:
            uploaded = self.upload_image(path, caption=content)
            if not uploaded.success:
                raise RuntimeError(uploaded.error_message or "Facebook image upload failed")
            media_ids.append(uploaded.post_id)
        return self._post(f"/{self._page_id}/feed", {"message": content, "attached_media": [{"media_fbid": mid} for mid in media_ids]})

    def upload_image(self, image_path: str, caption: str = "") -> PublishResult:
        result = PublishResult(platform="facebook")
        try:
            if image_path.startswith(("http://", "https://")):
                payload = self._post(f"/{self._page_id}/photos", {"url": image_path, "caption": caption, "published": "false"})
            else:
                payload = self._upload_local_image(image_path, caption)
            if payload.get("id"):
                result.success = True; result.post_id = str(payload["id"]); result.metadata = {"media_type": "image"}
            else:
                result.error_message = str(payload.get("error") or payload)
        except Exception as exc:
            result.error_message = str(exc)
        return result

    def _upload_local_image(self, path: str, caption: str) -> Dict[str, Any]:
        import mimetypes
        boundary = "----UCOSBoundary"
        filename = os.path.basename(path)
        mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        with open(path, "rb") as handle:
            content = handle.read()
        prefix = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="source"; filename="{filename}"\r\n'
            f"Content-Type: {mime}\r\n\r\n"
        ).encode()
        suffix = (
            f"\r\n--{boundary}\r\n"
            'Content-Disposition: form-data; name="published"\r\n\r\n'
            "false\r\n"
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="message"\r\n\r\n'
            f"{caption}\r\n"
            f"--{boundary}--\r\n"
        ).encode()
        body = prefix + content + suffix
        request = urllib.request.Request(f"{self.API_BASE}/{self._page_id}/photos", data=body, method="POST")
        request.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        request.add_header("Authorization", f"Bearer {self._access_token}")
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))

    def edit(self, post_id: str, content: str, **kwargs: Any) -> PublishResult:
        result = PublishResult(platform="facebook")
        try:
            payload = self._post(f"/{post_id}", {"message": content})
            if payload.get("success"):
                result.success = True; result.post_id = post_id
            else: result.error_message = str(payload.get("error") or payload)
        except Exception as exc: result.error_message = str(exc)
        return result

    def delete(self, post_id: str) -> bool:
        try: return bool(self._delete(f"/{post_id}").get("success"))
        except Exception: return False

    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        try: return self._api_get(f"/{post_id}", {"fields": "id,message,created_time,shares,reactions.summary(true),comments.summary(true)"})
        except Exception: return None

    def get_status(self, post_id: str) -> str:
        return "published" if self.get_post(post_id) else "unknown"

    def get_analytics(self, post_id: str) -> Dict[str, Any]:
        post = self.get_post(post_id)
        if not post: return {"post_id": post_id, "error": "analytics_unavailable"}
        reactions = post.get("reactions", {}).get("summary", {}).get("total_count", 0)
        comments = post.get("comments", {}).get("summary", {}).get("total_count", 0)
        shares = post.get("shares", {}).get("count", 0)
        return {"post_id": post_id, "reactions_count": reactions, "comments_count": comments, "shares_count": shares, "engagement_total": reactions + comments + shares}

    def schedule(self, content: str, scheduled_time: float, media_paths: Optional[List[str]] = None, **kwargs: Any) -> PublishResult:
        result = PublishResult(platform="facebook")
        try:
            payload = self._post(f"/{self._page_id}/feed", {"message": content, "published": "false", "scheduled_publish_time": int(scheduled_time)})
            if payload.get("id"):
                result.success = True; result.post_id = str(payload["id"]); result.metadata = {"scheduled_time": int(scheduled_time)}
            else: result.error_message = str(payload.get("error") or payload)
        except Exception as exc: result.error_message = str(exc)
        return result

    def get_page_info(self) -> Dict[str, Any]:
        try: return self._api_get(f"/{self._page_id}", {"fields": "id,name,fan_count,followers_count,category"})
        except Exception: return {}

    def get_stats(self) -> Dict[str, Any]:
        return {"platform": "facebook", "authenticated": self._authenticated, "page_id": self._page_id, "total_requests": self._request_count, "successful": self._success_count, "errors": self._error_count, "rate_limit_remaining": self._rate_limit_remaining}

    def _api_get(self, path: str, params: Optional[Dict[str, Any]] = None, token: Optional[str] = None) -> Dict[str, Any]:
        query = dict(params or {}); query["access_token"] = token or self._access_token
        url = f"{self.API_BASE}{path}?{urllib.parse.urlencode(query)}"
        request = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(request, timeout=30) as response: return json.loads(response.read().decode("utf-8"))

    def _post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(data); payload["access_token"] = self._access_token
        if "attached_media" in payload:
            payload["attached_media"] = json.dumps(payload["attached_media"], separators=(",", ":"))
        request = urllib.request.Request(f"{self.API_BASE}{path}", data=urllib.parse.urlencode(payload).encode("utf-8"), method="POST")
        with urllib.request.urlopen(request, timeout=60) as response: return json.loads(response.read().decode("utf-8"))

    def _delete(self, path: str) -> Dict[str, Any]:
        url = f"{self.API_BASE}{path}?{urllib.parse.urlencode({'access_token': self._access_token})}"
        with urllib.request.urlopen(urllib.request.Request(url, method="DELETE"), timeout=30) as response: return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _http_error(exc: urllib.error.HTTPError) -> str:
        try:
            payload = json.loads(exc.read().decode("utf-8")); return str(payload.get("error", {}).get("message") or payload)
        except Exception: return f"Facebook HTTP {exc.code}: {exc.reason}"
