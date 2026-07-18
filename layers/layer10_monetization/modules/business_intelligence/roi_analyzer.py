"""ROIAnalyzer — Calculate ROI, ROAS, CPA, and other business metrics."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_ROI_COUNTER = itertools.count(1)


class ROISnapshot:
    """A snapshot of ROI calculations."""

    __slots__ = ("snapshot_id", "platform", "roi", "roas", "cpa", "cpm",
                 "cpc", "cpl", "profit_margin", "ltv", "calculated_at")

    def __init__(self, platform: str = "") -> None:
        self.snapshot_id: str = f"roi_{next(_ROI_COUNTER)}"
        self.platform = platform
        self.roi: float = 0.0
        self.roas: float = 0.0
        self.cpa: float = 0.0
        self.cpm: float = 0.0
        self.cpc: float = 0.0
        self.cpl: float = 0.0
        self.profit_margin: float = 0.0
        self.ltv: float = 0.0
        self.calculated_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"snapshot_id": self.snapshot_id, "platform": self.platform,
                "roi": round(self.roi, 4), "roas": round(self.roas, 4),
                "cpa": round(self.cpa, 2), "cpm": round(self.cpm, 2),
                "profit_margin": round(self.profit_margin, 4)}


class ROIAnalyzer:
    """Calculate ROI, ROAS, CPA, CPM, CPC, CPL, profit margin, and LTV."""

    def __init__(self) -> None:
        self._snapshots: List[ROISnapshot] = []

    def calculate(self, platform: str, revenue: float, cost: float,
                  impressions: int = 0, clicks: int = 0,
                  conversions: int = 0, leads: int = 0,
                  customer_lifespan_months: int = 12,
                  monthly_revenue_per_customer: float = 0.0) -> ROISnapshot:
        snap = ROISnapshot(platform)
        if cost > 0:
            snap.roi = round((revenue - cost) / cost, 4)
            snap.roas = round(revenue / cost, 4)
        if conversions > 0:
            snap.cpa = round(cost / conversions, 2)
        if impressions > 0:
            snap.cpm = round((cost / impressions) * 1000, 2)
        if clicks > 0:
            snap.cpc = round(cost / clicks, 2)
        if leads > 0:
            snap.cpl = round(cost / leads, 2)
        if revenue > 0:
            snap.profit_margin = round((revenue - cost) / revenue, 4)
        if monthly_revenue_per_customer > 0:
            snap.ltv = round(monthly_revenue_per_customer * customer_lifespan_months, 2)
        self._snapshots.append(snap)
        return snap

    def calculate_batch(self, items: List[Dict[str, Any]]) -> List[ROISnapshot]:
        results = []
        for item in items:
            snap = self.calculate(
                platform=item.get("platform", ""),
                revenue=item.get("revenue", 0.0),
                cost=item.get("cost", 0.0),
                impressions=item.get("impressions", 0),
                clicks=item.get("clicks", 0),
                conversions=item.get("conversions", 0),
                leads=item.get("leads", 0),
            )
            results.append(snap)
        return results

    def compare_platforms(self) -> List[Dict[str, Any]]:
        by_platform: Dict[str, List[ROISnapshot]] = {}
        for s in self._snapshots:
            by_platform.setdefault(s.platform, []).append(s)
        results = []
        for platform, snaps in by_platform.items():
            avg_roi = sum(s.roi for s in snaps) / len(snaps)
            results.append({"platform": platform, "avg_roi": round(avg_roi, 4),
                            "snapshots": len(snaps)})
        return sorted(results, key=lambda x: x["avg_roi"], reverse=True)

    def get_trend(self, platform: str = "") -> List[Dict[str, Any]]:
        snaps = self._snapshots
        if platform:
            snaps = [s for s in snaps if s.platform == platform]
        return [{"roi": s.roi, "roas": s.roas, "timestamp": s.calculated_at}
                for s in snaps]

    def get_latest(self, platform: str = "") -> ROISnapshot:
        snaps = self._snapshots
        if platform:
            snaps = [s for s in snaps if s.platform == platform]
        return snaps[-1] if snaps else None

    def get_stats(self) -> Dict[str, Any]:
        if not self._snapshots:
            return {"total_snapshots": 0, "avg_roi": 0.0}
        avg_roi = sum(s.roi for s in self._snapshots) / len(self._snapshots)
        return {"total_snapshots": len(self._snapshots),
                "avg_roi": round(avg_roi, 4)}
