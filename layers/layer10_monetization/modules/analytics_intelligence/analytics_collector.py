"""AnalyticsCollector — Collect analytics from multiple sources."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

from layers.layer10_monetization.modules.analytics_intelligence.analytics_profile import AnalyticsProfile

_AC_COUNTER = itertools.count(1)


class CollectionTask:
    """A pending analytics collection task."""

    __slots__ = ("task_id", "platform", "post_ids", "status",
                 "results", "created_at", "completed_at")

    def __init__(self, platform: str = "", post_ids: Optional[List[str]] = None) -> None:
        self.task_id: str = f"act_{next(_AC_COUNTER)}"
        self.platform = platform
        self.post_ids = post_ids or []
        self.status: str = "pending"
        self.results: List[AnalyticsProfile] = []
        self.created_at: float = time.time()
        self.completed_at: Optional[float] = None


class AnalyticsCollector:
    """Collect analytics data from platform plugins."""

    def __init__(self) -> None:
        self._tasks: List[CollectionTask] = []
        self._profiles: List[AnalyticsProfile] = []

    def create_task(self, platform: str,
                    post_ids: Optional[List[str]] = None) -> CollectionTask:
        task = CollectionTask(platform, post_ids)
        self._tasks.append(task)
        return task

    def collect(self, platform: str, post_id: str,
                data: Optional[Dict[str, Any]] = None) -> AnalyticsProfile:
        profile = AnalyticsProfile(platform, post_id)
        if data:
            profile.impressions = data.get("impressions", 0)
            profile.reach = data.get("reach", 0)
            profile.likes = data.get("likes", 0)
            profile.comments = data.get("comments", 0)
            profile.shares = data.get("shares", 0)
            profile.saves = data.get("saves", 0)
            profile.clicks = data.get("clicks", 0)
            profile.views = data.get("views", 0)
            profile.revenue = data.get("revenue", 0.0)
            profile.conversions = data.get("conversions", 0)
        self._profiles.append(profile)
        return profile

    def collect_batch(self, platform: str,
                      items: List[Dict[str, Any]]) -> List[AnalyticsProfile]:
        return [self.collect(platform, item.get("post_id", ""), item)
                for item in items]

    def get_profiles(self, platform: str = "") -> List[AnalyticsProfile]:
        if platform:
            return [p for p in self._profiles if p.platform == platform]
        return list(self._profiles)

    def get_pending_tasks(self) -> List[CollectionTask]:
        return [t for t in self._tasks if t.status == "pending"]

    def get_stats(self) -> Dict[str, Any]:
        platforms: Dict[str, int] = {}
        for p in self._profiles:
            platforms[p.platform] = platforms.get(p.platform, 0) + 1
        return {"total_profiles": len(self._profiles),
                "total_tasks": len(self._tasks), "by_platform": platforms}
