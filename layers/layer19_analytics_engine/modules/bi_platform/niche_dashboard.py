"""NicheDashboard — Top niches, revenue by niche, growth, competition, opportunity."""
from __future__ import annotations
import threading
import time
from typing import Any, Dict, List, Optional


class NicheMetrics:
    __slots__ = ("name", "revenue", "clicks", "conversions", "accounts",
                 "posts", "growth_rate", "competition_score", "opportunity_score",
                 "trend", "updated_at")

    def __init__(self, name: str) -> None:
        self.name = name
        self.revenue = 0.0
        self.clicks = 0
        self.conversions = 0
        self.accounts = 0
        self.posts = 0
        self.growth_rate = 0.0
        self.competition_score = 50.0
        self.opportunity_score = 50.0
        self.trend = "stable"
        self.updated_at = time.time()

    @property
    def conversion_rate(self) -> float:
        return (self.conversions / self.clicks * 100) if self.clicks > 0 else 0.0

    @property
    def epc(self) -> float:
        return (self.revenue / self.clicks) if self.clicks > 0 else 0.0

    @property
    def revenue_per_post(self) -> float:
        return (self.revenue / self.posts) if self.posts > 0 else 0.0

    @property
    def overall_score(self) -> float:
        rev_score = min(self.revenue / 1000, 1.0) * 30
        growth_score = min(max(self.growth_rate, 0) / 50, 1.0) * 25
        opp_score = min(self.opportunity_score / 100, 1.0) * 25
        comp_bonus = max(1 - (self.competition_score / 100), 0) * 20
        return rev_score + growth_score + opp_score + comp_bonus

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "revenue": round(self.revenue, 2),
            "clicks": self.clicks, "conversions": self.conversions,
            "conversion_rate": round(self.conversion_rate, 2),
            "epc": round(self.epc, 4), "accounts": self.accounts,
            "posts": self.posts, "revenue_per_post": round(self.revenue_per_post, 2),
            "growth_rate": round(self.growth_rate, 1),
            "competition": round(self.competition_score, 1),
            "opportunity": round(self.opportunity_score, 1),
            "overall_score": round(self.overall_score, 1),
            "trend": self.trend,
        }


class NicheDashboard:
    """Analytics dashboard for niche performance comparison."""
    _instance: Optional["NicheDashboard"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "NicheDashboard":
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
        self._niches: Dict[str, NicheMetrics] = {}

    def update_niche(self, name: str, revenue: float = 0.0, clicks: int = 0,
                     conversions: int = 0, accounts: int = 0, posts: int = 0,
                     growth_rate: float = 0.0, competition: float = 50.0,
                     opportunity: float = 50.0) -> NicheMetrics:
        if name not in self._niches:
            self._niches[name] = NicheMetrics(name)
        nm = self._niches[name]
        nm.revenue += revenue
        nm.clicks += clicks
        nm.conversions += conversions
        nm.accounts = max(nm.accounts, accounts)
        nm.posts += posts
        nm.growth_rate = growth_rate
        nm.competition_score = competition
        nm.opportunity_score = opportunity
        nm.trend = "growing" if growth_rate > 5 else "declining" if growth_rate < -5 else "stable"
        nm.updated_at = time.time()
        return nm

    def get_niche(self, name: str) -> Optional[NicheMetrics]:
        return self._niches.get(name)

    def get_top_niches(self, limit: int = 10) -> List[NicheMetrics]:
        return sorted(self._niches.values(), key=lambda n: n.overall_score, reverse=True)[:limit]

    def get_by_revenue(self, limit: int = 10) -> List[NicheMetrics]:
        return sorted(self._niches.values(), key=lambda n: n.revenue, reverse=True)[:limit]

    def get_growing(self) -> List[NicheMetrics]:
        return sorted(
            [n for n in self._niches.values() if n.growth_rate > 5],
            key=lambda n: n.growth_rate, reverse=True,
        )

    def get_dashboard(self) -> Dict[str, Any]:
        niches = list(self._niches.values())
        total_revenue = sum(n.revenue for n in niches)
        return {
            "total_niches": len(niches),
            "total_revenue": round(total_revenue, 2),
            "avg_score": round(
                sum(n.overall_score for n in niches) / len(niches), 1
            ) if niches else 0,
            "growing": sum(1 for n in niches if n.trend == "growing"),
            "declining": sum(1 for n in niches if n.trend == "declining"),
            "revenue_share": {
                n.name: round(n.revenue / total_revenue * 100, 1) if total_revenue > 0 else 0
                for n in niches
            },
            "top_10": [n.to_dict() for n in self.get_top_niches(10)],
        }

    def stats(self) -> Dict[str, Any]:
        return {"niches": len(self._niches)}


def get_niche_dashboard() -> NicheDashboard:
    return NicheDashboard()
