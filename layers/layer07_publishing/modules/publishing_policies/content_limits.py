"""Content Limits — Platform-specific content limits (length, media, etc.)."""
from __future__ import annotations
from typing import Any, Dict


class ContentLimits:
    """Platform-specific content limits."""

    DEFAULT_LIMITS: Dict[str, Dict[str, Any]] = {
        "facebook": {
            "max_text_length": 63206,
            "max_images": 10,
            "max_hashtags": 30,
            "max_video_duration": 14400,
            "supports_carousel": True,
            "supports_stories": True,
        },
        "instagram": {
            "max_text_length": 2200,
            "max_images": 10,
            "max_hashtags": 30,
            "max_video_duration": 3600,
            "supports_carousel": True,
            "supports_reels": True,
        },
        "twitter": {
            "max_text_length": 280,
            "max_images": 4,
            "max_hashtags": 10,
            "max_video_duration": 140,
            "supports_threads": True,
        },
        "linkedin": {
            "max_text_length": 3000,
            "max_images": 9,
            "max_hashtags": 5,
            "max_article_length": 110000,
            "supports_carousel": True,
        },
        "youtube": {
            "max_title_length": 100,
            "max_description_length": 5000,
            "max_tags": 500,
            "max_video_duration": 43200,
        },
        "tiktok": {
            "max_text_length": 2200,
            "max_hashtags": 100,
            "max_video_duration": 600,
        },
        "pinterest": {
            "max_text_length": 500,
            "max_board_pins": 200000,
        },
        "reddit": {
            "max_title_length": 300,
            "max_text_length": 40000,
        },
    }

    def __init__(self) -> None:
        self._limits: Dict[str, Dict[str, Any]] = dict(self.DEFAULT_LIMITS)

    def get_limits(self, platform: str) -> Dict[str, Any]:
        return dict(self._limits.get(platform.lower(), {}))

    def get_limit(self, platform: str, key: str, default: Any = None) -> Any:
        return self._limits.get(platform.lower(), {}).get(key, default)

    def set_limit(self, platform: str, key: str, value: Any) -> None:
        platform = platform.lower()
        if platform not in self._limits:
            self._limits[platform] = {}
        self._limits[platform][key] = value

    def check_text_length(self, platform: str, text: str) -> bool:
        max_len = self.get_limit(platform, "max_text_length")
        if max_len is None:
            return True
        return len(text) <= max_len

    def check_image_count(self, platform: str, count: int) -> bool:
        max_imgs = self.get_limit(platform, "max_images")
        if max_imgs is None:
            return True
        return count <= max_imgs

    def check_hashtag_count(self, platform: str, count: int) -> bool:
        max_tags = self.get_limit(platform, "max_hashtags")
        if max_tags is None:
            return True
        return count <= max_tags

    def get_supported_platforms(self) -> list:
        return list(self._limits.keys())
