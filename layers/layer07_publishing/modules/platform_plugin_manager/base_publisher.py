"""Base Publisher — Frozen ABC interface that all platform plugins implement."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class PublishResult:
    """Result of a publish operation."""

    __slots__ = ("success", "post_id", "url", "platform", "error_message", "metadata")

    def __init__(self, success: bool = False, platform: str = "") -> None:
        self.success = success
        self.post_id: str = ""
        self.url: str = ""
        self.platform = platform
        self.error_message: str = ""
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "post_id": self.post_id,
            "url": self.url,
            "platform": self.platform,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


class PlatformCapabilities:
    """Capabilities of a platform plugin."""

    __slots__ = ("supports_images", "supports_video", "supports_carousel",
                 "supports_scheduled", "supports_edit", "supports_delete",
                 "supports_analytics", "supports_threads", "supports_stories",
                 "supports_polls", "max_length", "max_images",
                 "features")

    def __init__(self) -> None:
        self.supports_images: bool = False
        self.supports_video: bool = False
        self.supports_carousel: bool = False
        self.supports_scheduled: bool = False
        self.supports_edit: bool = False
        self.supports_delete: bool = False
        self.supports_analytics: bool = False
        self.supports_threads: bool = False
        self.supports_stories: bool = False
        self.supports_polls: bool = False
        self.max_length: int = 10000
        self.max_images: int = 0
        self.features: List[str] = []

    def supports(self, feature: str) -> bool:
        return getattr(self, f"supports_{feature}", False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "supports_images": self.supports_images,
            "supports_video": self.supports_video,
            "supports_carousel": self.supports_carousel,
            "supports_scheduled": self.supports_scheduled,
            "supports_edit": self.supports_edit,
            "supports_delete": self.supports_delete,
            "supports_analytics": self.supports_analytics,
            "supports_threads": self.supports_threads,
            "supports_stories": self.supports_stories,
            "supports_polls": self.supports_polls,
            "max_length": self.max_length,
            "max_images": self.max_images,
            "features": self.features,
        }


class BasePublisher(ABC):
    """Frozen abstract interface for all platform publishers.

    Every platform plugin MUST implement these methods.
    Interface is frozen — do not add new abstract methods
    without a major version bump.
    """

    @abstractmethod
    def get_platform_name(self) -> str:
        """Return platform identifier (e.g. 'facebook', 'linkedin')."""

    @abstractmethod
    def get_capabilities(self) -> PlatformCapabilities:
        """Return platform capabilities."""

    @abstractmethod
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with platform. Returns True if successful."""

    @abstractmethod
    def validate(self, content: str, content_type: str = "post") -> bool:
        """Validate content meets platform requirements."""

    @abstractmethod
    def publish(self, content: str, media_paths: Optional[List[str]] = None,
                content_type: str = "post", **kwargs: Any) -> PublishResult:
        """Publish content to the platform."""

    @abstractmethod
    def edit(self, post_id: str, content: str, **kwargs: Any) -> PublishResult:
        """Edit previously published content."""

    @abstractmethod
    def delete(self, post_id: str) -> bool:
        """Delete published content."""

    @abstractmethod
    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve post details."""

    @abstractmethod
    def get_status(self, post_id: str) -> str:
        """Get post status (published, scheduled, failed, deleted)."""

    @abstractmethod
    def get_analytics(self, post_id: str) -> Dict[str, Any]:
        """Get engagement analytics for a post."""

    @abstractmethod
    def schedule(self, content: str, scheduled_time: float,
                 media_paths: Optional[List[str]] = None, **kwargs: Any) -> PublishResult:
        """Schedule content for future publishing."""
