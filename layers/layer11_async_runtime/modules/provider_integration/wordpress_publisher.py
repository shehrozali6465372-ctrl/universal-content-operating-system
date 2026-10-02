"""L11 WordPress provider adapter for shared L07 publication gateway."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from .config import IntegrationConfig
from .http_client import HTTPClient


@dataclass
class ProviderPublishResult:
    success: bool = False
    platform: str = "wordpress"
    post_id: str = ""
    url: str = ""
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class WordPressPublisher:
    """WordPress REST adapter; publication policy remains owned by L07."""

    def __init__(self) -> None:
        self.config = IntegrationConfig.from_env()
        self.http = HTTPClient(self.config.http_timeout_seconds, self.config.http_max_retries)
        self._authenticated = False
        self._base_url = ""
        self._username = ""
        self._application_password = ""

    def get_platform_name(self) -> str:
        return "wordpress"

    def get_capabilities(self):
        class Capabilities:
            supports_images = False
            supports_video = False
            supports_carousel = False
            supports_scheduled = True
            supports_edit = True
            supports_delete = True
            supports_analytics = False
            supports_threads = False
            supports_stories = False
            supports_polls = False
            max_length = 1000000
            max_images = 0
            features = ["posts", "schedule", "rest_api"]

            def supports(self, feature: str) -> bool:
                return bool(getattr(self, f"supports_{feature}", False))

            def to_dict(self) -> Dict[str, Any]:
                return {k: getattr(self, k) for k in (
                    "supports_images", "supports_video", "supports_carousel",
                    "supports_scheduled", "supports_edit", "supports_delete",
                    "supports_analytics", "supports_threads", "supports_stories",
                    "supports_polls", "max_length", "max_images", "features",
                )}

        return Capabilities()

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        base = str(credentials.get("url") or credentials.get("base_url") or self.config.wordpress_url).strip().rstrip("/")
        username = str(credentials.get("username") or self.config.wordpress_username).strip()
        password = str(credentials.get("application_password") or self.config.wordpress_application_password).strip()
        if not base or not username or not password:
            return False
        self._base_url = base
        self._username = username
        self._application_password = password
        response = self.http.request(
            "GET",
            urljoin(self._base_url + "/", "wp-json/wp/v2/users/me"),
            headers=self._auth_header(),
            accepted_statuses=(200,),
        )
        return isinstance(response.data, dict) and bool(response.data.get("id"))

    def validate(self, content: str, content_type: str = "post") -> bool:
        return bool(str(content or "").strip()) and content_type in {"post", "article"}

    def publish(
        self,
        content: str,
        media_paths: Optional[List[str]] = None,
        content_type: str = "post",
        **kwargs: Any,
    ) -> ProviderPublishResult:
        if not self._authenticated:
            return self._failure("provider is not authenticated", "confirmed_failure")
        if not self.validate(content, content_type):
            return self._failure("content validation failed", "confirmed_failure")
        status = str(kwargs.get("status") or "publish").strip().lower()
        if status not in {"draft", "publish", "pending", "private", "future"}:
            return self._failure("unsupported WordPress status", "confirmed_failure")
        body = {
            "title": str(kwargs.get("title") or "UCOS Publication"),
            "content": content,
            "status": status,
        }
        if kwargs.get("date"):
            body["date"] = kwargs["date"]
        try:
            response = self.http.request(
                "POST",
                urljoin(self._base_url + "/", "wp-json/wp/v2/posts"),
                headers=self._auth_header(),
                json_body=body,
                accepted_statuses=(201,),
            )
        except Exception as exc:
            return self._failure(f"WordPress transport failed: {type(exc).__name__}", "unknown")
        data = response.data if isinstance(response.data, dict) else {}
        post_id = str(data.get("id") or "").strip()
        if not post_id:
            return self._failure("WordPress reported success without a post id", "unknown")
        return ProviderPublishResult(
            success=True,
            post_id=post_id,
            url=str(data.get("link") or ""),
            metadata={"provider_status": status, "provider": "wordpress"},
        )

    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        if not self._authenticated:
            return None
        response = self.http.request(
            "GET",
            urljoin(self._base_url + "/", f"wp-json/wp/v2/posts/{post_id}"),
            headers=self._auth_header(),
            accepted_statuses=(200,),
        )
        return response.data if isinstance(response.data, dict) else None

    def get_status(self, post_id: str) -> str:
        post = self.get_post(post_id)
        return str((post or {}).get("status") or "unknown")

    def get_analytics(self, post_id: str) -> Dict[str, Any]:
        return {}

    def edit(self, post_id: str, content: str, **kwargs: Any) -> ProviderPublishResult:
        if not self._authenticated:
            return self._failure("provider is not authenticated", "confirmed_failure")
        try:
            response = self.http.request(
                "POST",
                urljoin(self._base_url + "/", f"wp-json/wp/v2/posts/{post_id}"),
                headers=self._auth_header(),
                json_body={"content": content},
                accepted_statuses=(200,),
            )
        except Exception as exc:
            return self._failure(f"WordPress transport failed: {type(exc).__name__}", "unknown")
        data = response.data if isinstance(response.data, dict) else {}
        return ProviderPublishResult(
            success=bool(data.get("id")),
            post_id=str(data.get("id") or post_id),
            url=str(data.get("link") or ""),
            error_message="" if data.get("id") else "WordPress update returned no post id",
            metadata={"provider": "wordpress"},
        )

    def delete(self, post_id: str) -> bool:
        if not self._authenticated:
            return False
        try:
            response = self.http.request(
                "DELETE",
                urljoin(self._base_url + "/", f"wp-json/wp/v2/posts/{post_id}"),
                headers=self._auth_header(),
                params={"force": "true"},
                accepted_statuses=(200,),
            )
            return isinstance(response.data, dict) and bool(response.data.get("deleted"))
        except Exception:
            return False

    def schedule(self, content: str, scheduled_time: float, media_paths: Optional[List[str]] = None, **kwargs: Any) -> ProviderPublishResult:
        from datetime import datetime, timezone
        return self.publish(
            content,
            media_paths,
            kwargs.get("content_type", "post"),
            title=kwargs.get("title") or "UCOS Publication",
            status="future",
            date=datetime.fromtimestamp(float(scheduled_time), timezone.utc).isoformat(),
        )

    def _auth_header(self) -> Dict[str, str]:
        import base64
        token = base64.b64encode(
            f"{self._username}:{self._application_password}".encode("utf-8")
        ).decode("ascii")
        return {"Authorization": f"Basic {token}"}

    def _failure(self, message: str, outcome: str) -> ProviderPublishResult:
        return ProviderPublishResult(
            success=False,
            error_message=message[:500],
            metadata={"outcome": outcome, "provider": "wordpress"},
        )
