"""Performance Memory — Track reach, CTR, conversion, ROI history."""
from __future__ import annotations
from typing import Any, Dict, List


class PerformanceSnapshot:
    """A point-in-time performance measurement."""

    __slots__ = ("platform", "post_id", "reach", "ctr",
                 "conversion_rate", "revenue", "cost", "timestamp")

    def __init__(self, platform: str = "", post_id: str = "") -> None:
        self.platform = platform
        self.post_id = post_id
        self.reach: float = 0.0
        self.ctr: float = 0.0
        self.conversion_rate: float = 0.0
        self.revenue: float = 0.0
        self.cost: float = 0.0
        self.timestamp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "post_id": self.post_id,
            "reach": self.reach,
            "ctr": round(self.ctr, 3),
            "conversion_rate": round(self.conversion_rate, 3),
            "revenue": round(self.revenue, 2),
            "cost": round(self.cost, 2),
        }


class PerformanceMemory:
    """Track performance metrics over time for optimization."""

    def __init__(self) -> None:
        self._snapshots: List[PerformanceSnapshot] = []
        self._platform_reach: Dict[str, List[float]] = {}
        self._platform_ctr: Dict[str, List[float]] = {}

    def record(self, snapshot: PerformanceSnapshot) -> None:
        self._snapshots.append(snapshot)
        self._platform_reach.setdefault(snapshot.platform, []).append(snapshot.reach)
        self._platform_ctr.setdefault(snapshot.platform, []).append(snapshot.ctr)

    def get_avg_reach(self, platform: str = "") -> float:
        reaches = self._platform_reach.get(platform, [])
        return round(sum(reaches) / max(1, len(reaches)), 2)

    def get_avg_ctr(self, platform: str = "") -> float:
        ctrs = self._platform_ctr.get(platform, [])
        return round(sum(ctrs) / max(1, len(ctrs)), 3)

    def get_total_revenue(self) -> float:
        return round(sum(s.revenue for s in self._snapshots), 2)

    def get_total_cost(self) -> float:
        return round(sum(s.cost for s in self._snapshots), 2)

    def get_roi(self) -> float:
        total_cost = self.get_total_cost()
        if total_cost <= 0:
            return 0.0
        return round((self.get_total_revenue() - total_cost) / total_cost, 3)

    def get_best_platform(self, metric: str = "reach") -> str:
        if not self._platform_reach:
            return ""
        if metric == "reach":
            return max(self._platform_reach, key=lambda p: self.get_avg_reach(p))
        if metric == "ctr":
            return max(self._platform_ctr, key=lambda p: self.get_avg_ctr(p))
        return ""

    def get_snapshots(self, platform: str = "") -> List[PerformanceSnapshot]:
        if platform:
            return [s for s in self._snapshots if s.platform == platform]
        return list(self._snapshots)

    @property
    def snapshot_count(self) -> int:
        return len(self._snapshots)
