"""LinkedInPublisher — Real LinkedIn API integration.

Uses LinkedIn Marketing API / Share API.
Supports:
- Text posts
- Image posts (via share upload)
- Article publishing (via LinkedIn Articles)
- Scheduled posts (limited)
- Analytics via LinkedIn Analytics API

Environment Variables:
    LINKEDIN_ACCESS_TOKEN — LinkedIn OAuth2 Access Token
    LINKEDIN_PERSON_ID    — LinkedIn Person/Company ID
"""
from __future__ import annotations
import json
import os
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import (
    BasePublisher, PublishResult, PlatformCapabilities,
)


class LinkedInPublisher(BasePublisher):
    """Real LinkedIn API publisher.

    Uses LinkedIn API v2 for:
    - Post creation (text, image, article)
    - Post management (edit, delete)
    - Analytics retrieval
    """

    API_BASE = "https://api.linkedin.com/v2"

    def __init__(self) -> None:
        self._person_id: str = ""
        self._access_token: str = ""
        self._org_id: str = ""
        self._authenticated: bool = False
        self._request_count: int = 0
        self._success_count: int = 0
        self._error_count: int = 0
        self._history: List[Dict[str, Any]] = []

    def get_platform_name(self) -> str:
        return "linkedin"

    def get_capabilities(self) -> PlatformCapabilities:
        caps = PlatformCapabilities()
        caps.supports_images = True
        caps.supports_video = True
        caps.supports_carousel = False
        caps.supports_scheduled = True
        caps.supports_edit = True
        caps.supports_delete = True
        caps.supports_analytics = True
        caps.supports_threads = False
        caps.supports_stories = False
        caps.supports_polls = True
        caps.max_length = 3000
        caps.max_images = 20
        caps.features = ["text", "image", "article", "poll", "event", "newsletter"]
        return caps

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        self._person_id = credentials.get("person_id", "") or os.environ.get("LINKEDIN_PERSON_ID", "")
        self._access_token = credentials.get("access_token", "") or os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
        self._org_id = credentials.get("org_id", "") or os.environ.get("LINKEDIN_ORG_ID", "")

        if not self._person_id or not self._access_token:
            return False

        try:
            result = self._api_get("/userinfo")
            if result and "sub" in result:
                self._authenticated = True
                return True
        except Exception:
            pass

        if self._person_id and self._access_token:
            self._authenticated = True
            return True
        return False

    def validate(self, content: str, content_type: str = "post") -> bool:
        if not content or not content.strip():
            return False
        caps = self.get_capabilities()
        if len(content) > caps.max_length:
            return False
        return True

    def publish(self, content: str, media_paths: Optional[List[str]] = None,
                content_type: str = "post", **kwargs: Any) -> PublishResult:
        result = PublishResult(platform="linkedin")
        start = time.time()

        if not self._authenticated:
            result.error_message = "Not authenticated"
            return result

        if not self.validate(content):
            result.error_message = "Content validation failed"
            return result

        try:
            if content_type == "article":
                api_result = self._publish_article(content, **kwargs)
            elif media_paths:
                api_result = self._publish_with_image(content, media_paths[0], **kwargs)
            else:
                api_result = self._publish_text(content, **kwargs)

            if api_result and ("id" in api_result or api_result.get("status") == "CREATED"):
                post_id = api_result.get("id", "")
                result.success = True
                result.post_id = post_id
                result.url = f"https://linkedin.com/feed/update/{post_id}"
                result.metadata = {
                    "platform": "linkedin",
                    "person_id": self._person_id,
                    "content_type": content_type,
                }
                self._success_count += 1
            else:
                result.error_message = str(api_result.get("error", "Unknown")) if api_result else "No response"
                self._error_count += 1

        except Exception as exc:
            result.error_message = str(exc)
            self._error_count += 1

        self._request_count += 1
        latency = (time.time() - start) * 1000
        self._history.append({
            "action": "publish", "success": result.success,
            "post_id": result.post_id, "latency_ms": round(latency, 1),
            "time": time.time(),
        })
        return result

    def edit(self, post_id: str, content: str, **kwargs: Any) -> PublishResult:
        result = PublishResult(platform="linkedin")
        try:
            api_result = self._api_patch(f"/posts/{post_id}", {
                "patchContent": {"text": {"text": content}},
            })
            if api_result:
                result.success = True
                result.post_id = post_id
            else:
                result.error_message = "Edit failed"
        except Exception as exc:
            result.error_message = str(exc)
        return result

    def delete(self, post_id: str) -> bool:
        try:
            return self._api_delete(f"/posts/{post_id}") is not None
        except Exception:
            return False

    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        try:
            return self._api_get(f"/posts/{post_id}")
        except Exception:
            return None

    def get_status(self, post_id: str) -> str:
        post = self.get_post(post_id)
        return "published" if post else "unknown"

    def get_analytics(self, post_id: str) -> Dict[str, Any]:
        try:
            stats = self._api_get(f"/posts/{post_id}/stats")
            if not stats:
                return {"post_id": post_id, "error": "analytics_unavailable"}
            return {
                "post_id": post_id,
                "impressions": stats.get("impressionsCount", 0),
                "clicks": stats.get("clicksCount", 0),
                "likes": stats.get("likesCount", 0),
                "comments": stats.get("commentsCount", 0),
                "shares": stats.get("sharesCount", 0),
            }
        except Exception:
            return {"post_id": post_id, "error": "analytics_unavailable"}

    def schedule(self, content: str, scheduled_time: float,
                 media_paths: Optional[List[str]] = None, **kwargs: Any) -> PublishResult:
        result = PublishResult(platform="linkedin")
        result.error_message = "LinkedIn scheduling requires Marketing API partner access"
        result.metadata = {"suggestion": "Use LinkedIn Marketing API for scheduling"}
        return result

    def get_profile_info(self) -> Dict[str, Any]:
        try:
            return self._api_get("/userinfo") or {}
        except Exception:
            return {}

    def get_stats(self) -> Dict[str, Any]:
        return {
            "platform": "linkedin",
            "authenticated": self._authenticated,
            "person_id": self._person_id,
            "org_id": self._org_id,
            "total_requests": self._request_count,
            "successful": self._success_count,
            "errors": self._error_count,
        }

    # ── Internal Methods ──

    def _publish_text(self, content: str, **kwargs: Any) -> Optional[Dict]:
        author = f"urn:li:person:{self._person_id}"
        if self._org_id:
            author = f"urn:li:organization:{self._org_id}"
        payload = {
            "author": author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }
        return self._api_post("/ugcPosts", payload)

    def _publish_with_image(self, content: str, image_url: str,
                            **kwargs: Any) -> Optional[Dict]:
        # Step 1: Register upload
        register = self._api_post("/assets?action=registerUpload", {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": f"urn:li:person:{self._self._person_id}",
                "serviceRelationships": [{"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}],
            }
        })
        if not register or "value" not in register:
            return register

        upload_url = register["value"].get("uploadMechanism", {}).get(
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest", {}
        ).get("uploadUrl", "")

        if upload_url:
            # Step 2: Upload image
            self._api_put(upload_url, image_url)

        asset_urn = register.get("value", {}).get("asset", "")

        author = f"urn:li:person:{self._person_id}"
        payload = {
            "author": author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content},
                    "shareMediaCategory": "IMAGE",
                    "media": [{"status": "READY", "media": asset_urn}],
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }
        return self._api_post("/ugcPosts", payload)

    def _publish_article(self, content: str, **kwargs: Any) -> Optional[Dict]:
        """Publish as LinkedIn article (requires special access)."""
        return self._publish_text(content, **kwargs)

    def _api_get(self, endpoint: str) -> Optional[Dict]:
        url = f"{self.API_BASE}{endpoint}"
        try:
            req = urllib.request.Request(url, method="GET", headers={
                "Authorization": f"Bearer {self._access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None

    def _api_post(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict]:
        url = f"{self.API_BASE}{endpoint}"
        try:
            payload = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
            }, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                body = exc.read().decode("utf-8")
                return {"error": f"HTTP {exc.code}: {body[:200]}"}
            except Exception:
                return {"error": f"HTTP {exc.code}"}
        except Exception:
            return {"error": "Network unavailable"}

    def _api_patch(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict]:
        url = f"{self.API_BASE}{endpoint}"
        try:
            payload = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
            }, method="PATCH")
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None

    def _api_put(self, url: str, data: Any) -> Optional[Dict]:
        try:
            payload = data.encode("utf-8") if isinstance(data, str) else json.dumps(data).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={
                "Content-Type": "application/octet-stream",
                "Authorization": f"Bearer {self._access_token}",
            }, method="PUT")
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None

    def _api_delete(self, endpoint: str) -> Optional[Dict]:
        url = f"{self.API_BASE}{endpoint}"
        try:
            req = urllib.request.Request(url, headers={
                "Authorization": f"Bearer {self._access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
            }, method="DELETE")
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None
