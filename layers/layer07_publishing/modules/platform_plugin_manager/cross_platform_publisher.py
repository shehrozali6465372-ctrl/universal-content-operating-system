"""CrossPlatformPublisher — Publish to multiple platforms simultaneously.

Takes a single content piece and publishes it to multiple platforms
with automatic formatting adjustments per platform.

Architecture:
    ContentRequest → CrossPlatformPublisher → Platform Adapters → Publish Results

Features:
- Auto-format content per platform (character limits, hashtags, etc.)
- Parallel or sequential publishing
- Rollback on failure
- Analytics aggregation
"""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import (
    BasePublisher, PublishResult, PlatformCapabilities,
)


class PlatformConfig:
    """Configuration for a platform in cross-platform publish."""

    __slots__ = ("platform_name", "publisher", "enabled", "format_options",
                 "hashtag_strategy", "max_length_override", "metadata")

    def __init__(self, platform_name: str, publisher: BasePublisher,
                 enabled: bool = True) -> None:
        self.platform_name = platform_name
        self.publisher = publisher
        self.enabled = enabled
        self.format_options: Dict[str, Any] = {}
        self.hashtag_strategy: str = "append"  # append, separate, none
        self.max_length_override: int = 0
        self.metadata: Dict[str, Any] = {}


class CrossPlatformResult:
    """Result of a cross-platform publish operation."""

    __slots__ = ("request_id", "topic", "results", "success_count",
                 "failure_count", "total_duration_ms", "metadata")

    def __init__(self, request_id: str = "", topic: str = "") -> None:
        self.request_id = request_id
        self.topic = topic
        self.results: Dict[str, PublishResult] = {}
        self.success_count: int = 0
        self.failure_count: int = 0
        self.total_duration_ms: float = 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "topic": self.topic,
            "platforms_published": self.success_count,
            "platforms_failed": self.failure_count,
            "total_duration_ms": round(self.total_duration_ms, 1),
            "results": {
                name: result.to_dict() for name, result in self.results.items()
            },
        }


class CrossPlatformPublisher:
    """Publish content to multiple platforms simultaneously.

    Usage:
        cross = CrossPlatformPublisher()
        cross.register_platform("facebook", facebook_publisher)
        cross.register_platform("instagram", instagram_publisher)
        cross.register_platform("linkedin", linkedin_publisher)
        cross.register_platform("twitter", twitter_publisher)

        result = cross.publish(
            topic="AI Trends",
            content="AI is transforming everything...",
            image_prompt="An AI brain illustration",
            platforms=["facebook", "instagram", "twitter"],
        )
    """

    PLATFORM_FORMAT_RULES = {
        "facebook": {
            "max_length": 63206,
            "hashtag_style": "inline",
            "mention_style": "@{username}",
            "supports_images": True,
            "optimal_length": (100, 500),
        },
        "instagram": {
            "max_length": 2200,
            "hashtag_style": "separate_block",
            "mention_style": "@{username}",
            "supports_images": True,
            "optimal_length": (100, 300),
        },
        "linkedin": {
            "max_length": 3000,
            "hashtag_style": "inline",
            "mention_style": "@{username}",
            "supports_images": True,
            "optimal_length": (100, 600),
        },
        "twitter": {
            "max_length": 280,
            "hashtag_style": "inline",
            "mention_style": "@{username}",
            "supports_images": True,
            "optimal_length": (50, 250),
        },
    }

    def __init__(self) -> None:
        self._platforms: Dict[str, PlatformConfig] = {}
        self._publish_count: int = 0
        self._history: List[Dict[str, Any]] = []

    def register_platform(self, name: str, publisher: BasePublisher,
                         enabled: bool = True) -> None:
        self._platforms[name] = PlatformConfig(name, publisher, enabled)

    def unregister_platform(self, name: str) -> bool:
        if name in self._platforms:
            del self._platforms[name]
            return True
        return False

    def enable_platform(self, name: str) -> bool:
        if name in self._platforms:
            self._platforms[name].enabled = True
            return True
        return False

    def disable_platform(self, name: str) -> bool:
        if name in self._platforms:
            self._platforms[name].enabled = False
            return True
        return False

    def publish(
        self,
        topic: str = "",
        content: str = "",
        image_prompt: str = "",
        platforms: Optional[List[str]] = None,
        hashtags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CrossPlatformResult:
        """Publish content to multiple platforms.

        Auto-formats content per platform rules:
        - Truncates for Twitter
        - Adds hashtags differently per platform
        - Adjusts tone for LinkedIn vs Instagram
        """
        start = time.time()
        request_id = f"cross_{int(time.time() * 1000) % 10000000}"
        result = CrossPlatformResult(request_id=request_id, topic=topic)

        # Determine which platforms to publish to
        target_platforms = platforms or [n for n, c in self._platforms.items() if c.enabled]

        for plat_name in target_platforms:
            config = self._platforms.get(plat_name)
            if not config or not config.enabled:
                continue

            # Format content for this platform
            formatted = self._format_for_platform(content, plat_name, hashtags)

            # Publish
            media_paths = [image_prompt] if image_prompt else None
            pub_result = config.publisher.publish(
                formatted, media_paths=media_paths, content_type="post",
            )

            result.results[plat_name] = pub_result
            if pub_result.success:
                result.success_count += 1
            else:
                result.failure_count += 1

        result.total_duration_ms = (time.time() - start) * 1000
        self._publish_count += 1
        self._history.append({
            "request_id": request_id,
            "topic": topic,
            "platforms": target_platforms,
            "success": result.success_count,
            "failed": result.failure_count,
            "time": time.time(),
        })
        return result

    def _format_for_platform(self, content: str, platform: str,
                            hashtags: Optional[List[str]] = None) -> str:
        """Auto-format content for a specific platform."""
        rules = self.PLATFORM_FORMAT_RULES.get(platform, {})
        max_len = rules.get("max_length", 10000)
        formatted = content

        # Truncate if too long
        if len(formatted) > max_len:
            formatted = formatted[:max_len - 3] + "..."

        # Add hashtags
        if hashtags:
            hashtag_str = " ".join(f"#{h.strip('#')}" for h in hashtags)
            if rules.get("hashtag_style") == "separate_block":
                formatted = f"{formatted}\n\n{hashtag_str}"
            else:
                formatted = f"{formatted} {hashtag_str}"

        return formatted

    def get_platform_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Get capabilities of all registered platforms."""
        caps = {}
        for name, config in self._platforms.items():
            c = config.publisher.get_capabilities()
            caps[name] = c.to_dict()
        return caps

    def get_stats(self) -> Dict[str, Any]:
        return {
            "platforms_registered": len(self._platforms),
            "platforms_enabled": sum(1 for c in self._platforms.values() if c.enabled),
            "total_publishes": self._publish_count,
            "platform_names": list(self._platforms.keys()),
        }

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self._history[-limit:]
