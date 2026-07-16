"""Metrics Normalizer — Convert platform-specific metrics to unified format."""
from __future__ import annotations
from typing import Any, Dict, List

from layers.layer07_publishing.modules.analytics_hook.analytics_event import AnalyticsEvent

# Platform-specific field name mappings to unified names
PLATFORM_MAPPINGS: Dict[str, Dict[str, str]] = {
    "facebook": {
        "reactions": "likes", "total_reactions": "likes",
        "post_impressions": "impressions", "post_reach": "reach",
        "shares": "shares", "comments": "comments",
        "link_clicks": "link_clicks", "video_views": "views",
        "video_p95_watched_time": "watch_time",
    },
    "instagram": {
        "like_count": "likes", "comments_count": "comments",
        "shares": "shares", "saves": "saves",
        "impressions": "impressions", "reach": "reach",
        "plays": "views",
    },
    "twitter": {
        "favorite_count": "likes", "retweet_count": "shares",
        "reply_count": "comments", "quote_count": "quotes",
        "impression_count": "impressions",
    },
    "linkedin": {
        "like": "likes", "comment": "comments",
        "share": "shares", "click": "clicks",
        "impression": "impressions", "reach": "reach",
    },
    "youtube": {
        "likeCount": "likes", "commentCount": "comments",
        "viewCount": "views", "subscriberCount": "subscribers",
        "watchTimeMinutes": "watch_time",
    },
    "tiktok": {
        "like_count": "likes", "comment_count": "comments",
        "share_count": "shares", "play_count": "views",
        "digg_count": "likes",
    },
}

UNIFIED_METRICS = (
    "likes", "comments", "shares", "saves", "views",
    "impressions", "reach", "clicks", "link_clicks",
    "watch_time", "subscribers", "engagement_rate",
)


class MetricsNormalizer:
    """Normalize platform-specific metrics to a common format."""

    def __init__(self) -> None:
        self._normalization_count = 0

    def normalize(self, event: AnalyticsEvent) -> AnalyticsEvent:
        platform = event.platform.lower()
        mapping = PLATFORM_MAPPINGS.get(platform, {})
        normalized: Dict[str, Any] = {}
        for raw_key, value in event.metrics.items():
            if isinstance(value, (int, float)):
                unified_key = mapping.get(raw_key, raw_key)
                normalized[unified_key] = value
        event.metrics = normalized
        self._normalization_count += 1
        return event

    def normalize_batch(self, events: List[AnalyticsEvent]) -> List[AnalyticsEvent]:
        return [self.normalize(e) for e in events]

    def get_platform_mapping(self, platform: str) -> Dict[str, str]:
        return PLATFORM_MAPPINGS.get(platform.lower(), {})

    def supported_platforms(self) -> List[str]:
        return list(PLATFORM_MAPPINGS.keys())

    def compute_engagement_rate(self, event: AnalyticsEvent) -> float:
        likes = event.get("likes", 0)
        comments = event.get("comments", 0)
        shares = event.get("shares", 0)
        saves = event.get("saves", 0)
        reach = event.get("reach", 0) or event.get("impressions", 0)
        if reach <= 0:
            return 0.0
        return round((likes + comments + shares + saves) / reach * 100, 2)

    @property
    def normalization_count(self) -> int:
        return self._normalization_count
