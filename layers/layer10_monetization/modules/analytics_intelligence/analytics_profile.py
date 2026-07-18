"""AnalyticsProfile — Unified analytics data model."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict

_AP_COUNTER = itertools.count(1)


class AnalyticsProfile:
    """Unified analytics profile for any platform."""

    __slots__ = ("profile_id", "platform", "post_id", "content_type",
                 "impressions", "reach", "engagement_rate", "likes",
                 "comments", "shares", "saves", "clicks", "ctr",
                 "views", "watch_time", "completion_rate", "revenue",
                 "conversions", "metadata", "collected_at")

    def __init__(self, platform: str = "", post_id: str = "") -> None:
        self.profile_id: str = f"ap_{next(_AP_COUNTER)}"
        self.platform = platform
        self.post_id = post_id
        self.content_type: str = "post"
        self.impressions: int = 0
        self.reach: int = 0
        self.engagement_rate: float = 0.0
        self.likes: int = 0
        self.comments: int = 0
        self.shares: int = 0
        self.saves: int = 0
        self.clicks: int = 0
        self.ctr: float = 0.0
        self.views: int = 0
        self.watch_time: float = 0.0
        self.completion_rate: float = 0.0
        self.revenue: float = 0.0
        self.conversions: int = 0
        self.metadata: Dict[str, Any] = {}
        self.collected_at: float = time.time()

    def get_engagement_total(self) -> int:
        return self.likes + self.comments + self.shares + self.saves

    def get_engagement_rate_calc(self) -> float:
        if self.impressions == 0:
            return 0.0
        return round(self.get_engagement_total() / self.impressions, 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id, "platform": self.platform,
            "post_id": self.post_id, "content_type": self.content_type,
            "impressions": self.impressions, "reach": self.reach,
            "engagement_rate": round(self.engagement_rate, 4),
            "likes": self.likes, "comments": self.comments,
            "shares": self.shares, "saves": self.saves,
            "clicks": self.clicks, "ctr": round(self.ctr, 4),
            "views": self.views, "revenue": round(self.revenue, 2),
        }


class AnalyticsProfileBuilder:
    """Fluent builder for AnalyticsProfile."""

    def __init__(self, platform: str = "", post_id: str = "") -> None:
        self._profile = AnalyticsProfile(platform, post_id)

    def content_type(self, ct: str) -> "AnalyticsProfileBuilder":
        self._profile.content_type = ct
        return self

    def impressions(self, val: int) -> "AnalyticsProfileBuilder":
        self._profile.impressions = val
        return self

    def reach(self, val: int) -> "AnalyticsProfileBuilder":
        self._profile.reach = val
        return self

    def likes(self, val: int) -> "AnalyticsProfileBuilder":
        self._profile.likes = val
        return self

    def comments(self, val: int) -> "AnalyticsProfileBuilder":
        self._profile.comments = val
        return self

    def shares(self, val: int) -> "AnalyticsProfileBuilder":
        self._profile.shares = val
        return self

    def saves(self, val: int) -> "AnalyticsProfileBuilder":
        self._profile.saves = val
        return self

    def clicks(self, val: int) -> "AnalyticsProfileBuilder":
        self._profile.clicks = val
        return self

    def views(self, val: int) -> "AnalyticsProfileBuilder":
        self._profile.views = val
        return self

    def build(self) -> AnalyticsProfile:
        return self._profile
