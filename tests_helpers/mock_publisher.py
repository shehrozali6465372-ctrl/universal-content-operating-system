"""Mock Publisher — Test implementation of BasePublisher."""
from __future__ import annotations
import itertools
from typing import Any, Dict, List, Optional

from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import (
    BasePublisher, PublishResult, PlatformCapabilities,
)

_COUNTER = itertools.count(1)


class MockPublisher(BasePublisher):
    """Mock publisher for testing — implements full BasePublisher interface."""

    def __init__(self, platform: str = "mock") -> None:
        self._platform = platform
        self._authenticated = False
        self._posts: Dict[str, Dict[str, Any]] = {}

    def get_platform_name(self) -> str:
        return self._platform

    def get_capabilities(self) -> PlatformCapabilities:
        caps = PlatformCapabilities()
        caps.supports_images = True
        caps.supports_video = True
        caps.supports_scheduled = True
        caps.supports_edit = True
        caps.supports_delete = True
        caps.supports_analytics = True
        caps.max_length = 5000
        caps.max_images = 10
        caps.features = ["images", "video", "scheduled", "edit", "analytics"]
        return caps

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        self._authenticated = True
        return True

    def validate(self, content: str, content_type: str = "post") -> bool:
        return bool(content and len(content) > 0)

    def publish(self, content: str, media_paths: Optional[List[str]] = None,
                content_type: str = "post", **kwargs: Any) -> PublishResult:
        result = PublishResult(success=True, platform=self._platform)
        result.post_id = f"{self._platform}_{next(_COUNTER)}"
        result.url = f"https://{self._platform}.example.com/post/{result.post_id}"
        self._posts[result.post_id] = {"content": content, "type": content_type}
        return result

    def edit(self, post_id: str, content: str, **kwargs: Any) -> PublishResult:
        result = PublishResult(success=True, platform=self._platform)
        result.post_id = post_id
        if post_id in self._posts:
            self._posts[post_id]["content"] = content
        return result

    def delete(self, post_id: str) -> bool:
        return self._posts.pop(post_id, None) is not None

    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        return self._posts.get(post_id)

    def get_status(self, post_id: str) -> str:
        return "published" if post_id in self._posts else "not_found"

    def get_analytics(self, post_id: str) -> Dict[str, Any]:
        return {
            "post_id": post_id, "views": 100, "likes": 10,
            "shares": 5, "comments": 3,
        }

    def schedule(self, content: str, scheduled_time: float,
                 media_paths: Optional[List[str]] = None, **kwargs: Any) -> PublishResult:
        result = PublishResult(success=True, platform=self._platform)
        result.post_id = f"{self._platform}_scheduled_{next(_COUNTER)}"
        result.metadata["scheduled_time"] = scheduled_time
        self._posts[result.post_id] = {"content": content, "scheduled": True}
        return result
