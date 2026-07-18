"""AnalyticsNormalizer — Convert platform-specific metrics to common format."""
from __future__ import annotations
from typing import Any, Dict

# Platform-specific metric name mappings
PLATFORM_MAPPINGS: Dict[str, Dict[str, str]] = {
    "facebook": {
        "post_impressions": "impressions", "post_reach": "reach",
        " reactions": "likes", "post_engaged_users": "engagement",
    },
    "instagram": {
        "impressions": "impressions", "reach": "reach",
        "likes": "likes", "comments": "comments",
    },
    "x": {
        "impression_count": "impressions", "like_count": "likes",
        "retweet_count": "shares", "reply_count": "comments",
    },
    "linkedin": {
        "impressionCount": "impressions", "clickCount": "clicks",
        "likeCount": "likes", "commentCount": "comments",
        "shareCount": "shares",
    },
    "youtube": {
        "viewCount": "views", "likeCount": "likes",
        "commentCount": "comments",
    },
    "tiktok": {
        "play_count": "views", "like_count": "likes",
        "comment_count": "comments", "share_count": "shares",
    },
}

NORMALIZED_FIELDS = (
    "impressions", "reach", "likes", "comments", "shares",
    "saves", "clicks", "ctr", "views", "engagement_rate",
)


class AnalyticsNormalizer:
    """Convert platform-specific metric names to a unified format."""

    def __init__(self) -> None:
        self._normalizations: int = 0

    def normalize(self, platform: str, data: Dict[str, Any]) -> Dict[str, Any]:
        mapping = PLATFORM_MAPPINGS.get(platform.lower(), {})
        normalized: Dict[str, Any] = {"platform": platform}
        for raw_key, value in data.items():
            standard_key = mapping.get(raw_key, raw_key)
            normalized[standard_key] = value
        self._normalizations += 1
        return normalized

    def normalize_batch(self, platform: str,
                        items: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        return [self.normalize(platform, item) for item in items]

    def get_supported_platforms(self) -> list[str]:
        return list(PLATFORM_MAPPINGS.keys())

    def get_mapping(self, platform: str) -> Dict[str, str]:
        return dict(PLATFORM_MAPPINGS.get(platform.lower(), {}))

    def get_stats(self) -> Dict[str, Any]:
        return {"total_normalizations": self._normalizations,
                "supported_platforms": len(PLATFORM_MAPPINGS)}
