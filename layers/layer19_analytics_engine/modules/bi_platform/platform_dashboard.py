"""PlatformDashboard — Per-platform reach, engagement, clicks, revenue."""
from __future__ import annotations
import threading
import time
from typing import Any, Dict, List, Optional


class PlatformMetrics:
    __slots__ = ("platform", "reach", "engagement", "clicks", "conversions",
                 "revenue", "accounts", "posts", "avg_engagement_rate",
                 "follower_growth", "updated_at")

    def __init__(self, platform: str) -> None:
        self.platform = platform
        self.reach = 0
        self.engagement = 0
        self.clicks = 0
        self.conversions = 0
        self.revenue = 0.0
        self.accounts = 0
        self.posts = 0
        self.avg_engagement_rate = 0.0
        self.follower_growth = 0
        self.updated_at = time.time()

    @property
    def engagement_rate(self) -> float:
        return (self.engagement / self.reach * 100) if self.reach > 0 else 0.0

    @property
    def ctr(self) -> float:
        return (self.clicks / self.reach * 100) if self.reach > 0 else 0.0

    @property
    def rpm(self) -> float:
        return (self.revenue / self.reach * 1000) if self.reach > 0 else 0.0

    @property
    def revenue_per_post(self) -> float:
        return (self.revenue / self.posts) if self.posts > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform, "reach": self.reach,
            "engagement": self.engagement,
            "engagement_rate": round(self.engagement_rate, 2),
            "clicks": self.clicks, "conversions": self.conversions,
            "ctr": round(self.ctr, 2), "revenue": round(self.revenue, 2),
            "rpm": round(self.rpm, 2),
            "revenue_per_post": round(self.revenue_per_post, 2),
            "accounts": self.accounts, "posts": self.posts,
            "follower_growth": self.follower_growth,
        }


PLATFORMS = ["facebook", "instagram", "tiktok", "x", "youtube",
             "pinterest", "linkedin", "wordpress", "medium"]


class PlatformDashboard:
    """Analytics dashboard for per-platform performance comparison."""
    _instance: Optional["PlatformDashboard"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "PlatformDashboard":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._platforms: Dict[str, PlatformMetrics] = {}
        for p in PLATFORMS:
            self._platforms[p] = PlatformMetrics(p)

    def update_platform(self, platform: str, reach: int = 0, engagement: int = 0,
                        clicks: int = 0, conversions: int = 0, revenue: float = 0.0,
                        accounts: int = 0, posts: int = 0,
                        follower_growth: int = 0) -> PlatformMetrics:
        if platform not in self._platforms:
            self._platforms[platform] = PlatformMetrics(platform)
        pm = self._platforms[platform]
        pm.reach += reach
        pm.engagement += engagement
        pm.clicks += clicks
        pm.conversions += conversions
        pm.revenue += revenue
        pm.accounts = max(pm.accounts, accounts)
        pm.posts += posts
        pm.follower_growth += follower_growth
        pm.updated_at = time.time()
        return pm

    def get_platform(self, platform: str) -> Optional[PlatformMetrics]:
        return self._platforms.get(platform)

    def get_top_by_revenue(self, limit: int = 10) -> List[PlatformMetrics]:
        return sorted(self._platforms.values(), key=lambda p: p.revenue, reverse=True)[:limit]

    def get_top_by_engagement(self, limit: int = 10) -> List[PlatformMetrics]:
        return sorted(self._platforms.values(), key=lambda p: p.engagement_rate, reverse=True)[:limit]

    def get_dashboard(self) -> Dict[str, Any]:
        platforms = list(self._platforms.values())
        total_revenue = sum(p.revenue for p in platforms)
        total_reach = sum(p.reach for p in platforms)
        return {
            "total_platforms": len(platforms),
            "total_revenue": round(total_revenue, 2),
            "total_reach": total_reach,
            "revenue_by_platform": {
                p.platform: round(p.revenue, 2) for p in platforms if p.revenue > 0
            },
            "reach_by_platform": {
                p.platform: p.reach for p in platforms if p.reach > 0
            },
            "revenue_share": {
                p.platform: round(p.revenue / total_revenue * 100, 1) if total_revenue > 0 else 0
                for p in platforms
            },
            "platforms": [p.to_dict() for p in self.get_top_by_revenue()],
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "platforms": len(self._platforms),
            "active": sum(1 for p in self._platforms.values() if p.reach > 0),
        }


def get_platform_dashboard() -> PlatformDashboard:
    return PlatformDashboard()
