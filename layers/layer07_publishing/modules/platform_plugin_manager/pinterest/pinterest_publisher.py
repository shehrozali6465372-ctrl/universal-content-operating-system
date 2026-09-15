"""Pinterest API v5 publisher.

Requires account-scoped OAuth credentials with pins:write/pins:read and a
board_id. The current publisher implements image Pins only; it does not claim
video publishing or native scheduling.
"""
from __future__ import annotations
import json
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional
from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import BasePublisher, PublishResult, PlatformCapabilities


class PinterestPublisher(BasePublisher):
    API_BASE = "https://api.pinterest.com/v5"

    def __init__(self):
        self.token = ""
        self.board_id = ""
        self.authenticated = False

    def get_platform_name(self):
        return "pinterest"

    def get_capabilities(self):
        c = PlatformCapabilities()
        c.supports_images = True
        c.supports_video = False
        c.supports_delete = True
        c.supports_analytics = True
        c.max_length = 500
        c.features = ["pins", "boards", "analytics"]
        return c

    def authenticate(self, credentials):
        # Credentials are supplied by the account-scoped credential resolver.
        # Do not fall back to process-global Pinterest credentials: doing so can
        # silently publish one account's content through another account.
        self.token = str(credentials.get("access_token") or "")
        self.board_id = str(credentials.get("board_id") or "")
        if not self.token or not self.board_id:
            self.authenticated = False
            return False
        try:
            response = self._request("GET", "/user_account", None)
            self.authenticated = bool(response and response.get("username"))
        except Exception:
            self.authenticated = False
        return self.authenticated

    def validate(self, content, content_type="post"):
        return bool(content and len(content) <= 500 and self.board_id and content_type in {"post", "photo"})

    def publish(self, content, media_paths=None, content_type="post", **kwargs):
        result = PublishResult(platform="pinterest")
        if not self.authenticated:
            result.error_message = "Not authenticated"
            return result
        if not self.validate(content, content_type):
            result.error_message = "Pinterest validation failed"
            return result
        media_url = (media_paths or [""])[0]
        if not media_url.startswith(("http://", "https://")):
            result.error_message = "Pinterest image Pins require a publicly reachable media URL"
            return result
        body = {
            "board_id": self.board_id,
            "title": kwargs.get("title", content[:100]),
            "description": content,
            "media_source": {"source_type": "image_url", "url": media_url},
        }
        if kwargs.get("link"):
            body["link"] = kwargs["link"]
        try:
            data = self._request("POST", "/pins", body)
            if data and data.get("id"):
                pin_id = str(data["id"])
                result.success = True
                result.post_id = pin_id
                result.url = f"https://www.pinterest.com/pin/{pin_id}/"
                result.metadata = {"board_id": self.board_id}
            else:
                result.error_message = str(data or "Pinterest returned no pin id")
        except Exception as exc:
            result.error_message = str(exc)
        return result

    def edit(self, post_id, content, **kwargs):
        result = PublishResult(platform="pinterest")
        try:
            data = self._request("PATCH", f"/pins/{post_id}", {"description": content})
            result.success = bool(data and data.get("id"))
            result.post_id = str(post_id)
            result.url = f"https://www.pinterest.com/pin/{post_id}/"
            result.error_message = "" if result.success else str(data)
        except Exception as exc:
            result.error_message = str(exc)
        return result

    def delete(self, post_id):
        try:
            self._request("DELETE", f"/pins/{post_id}", None)
            return True
        except Exception:
            return False

    def get_post(self, post_id):
        try:
            return self._request("GET", f"/pins/{post_id}", None)
        except Exception:
            return None

    def get_status(self, post_id):
        return "published" if self.get_post(post_id) else "unknown"

    def get_analytics(self, post_id):
        # A Pin object is not analytics. Never reinterpret object metadata as
        # impressions/clicks/etc. until the required analytics endpoint is wired.
        return {"post_id": str(post_id), "analytics": "UNKNOWN"}

    def schedule(self, content, scheduled_time, media_paths=None, **kwargs):
        result = PublishResult(platform="pinterest")
        result.error_message = "Pinterest API publisher does not claim native scheduling"
        return result

    def _request(self, method, path, body):
        url = self.API_BASE + path
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
                return json.loads(raw.decode()) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:1000]
            raise RuntimeError(f"Pinterest HTTP {exc.code}: {detail}") from exc
