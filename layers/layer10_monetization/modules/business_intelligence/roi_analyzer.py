"""ROIAnalyzer — validated ROI/ROAS calculations."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_ROI_COUNTER = itertools.count(1)


class ROISnapshot:
    def __init__(self, platform: str = "") -> None:
        self.snapshot_id = f"roi_{next(_ROI_COUNTER)}"
        self.platform = platform
        self.roi = self.roas = self.cpa = self.cpm = self.cpc = self.cpl = 0.0
        self.profit_margin = self.ltv = 0.0
        self.calculated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"snapshot_id": self.snapshot_id, "platform": self.platform,
                "roi": round(self.roi, 4), "roas": round(self.roas, 4),
                "cpa": round(self.cpa, 2), "cpm": round(self.cpm, 2),
                "profit_margin": round(self.profit_margin, 4)}


class ROIAnalyzer:
    def __init__(self, max_snapshots: int = 10000) -> None:
        if max_snapshots <= 0:
            raise ValueError("max_snapshots must be positive")
        self._max_snapshots = max_snapshots
        self._snapshots: List[ROISnapshot] = []

    def calculate(self, platform: str, revenue: float, cost: float,
                  impressions: int = 0, clicks: int = 0, conversions: int = 0,
                  leads: int = 0, customer_lifespan_months: int = 12,
                  monthly_revenue_per_customer: float = 0.0) -> ROISnapshot:
        values = (revenue, cost, monthly_revenue_per_customer)
        if any(value < 0 for value in values) or any(
            value < 0 for value in (impressions, clicks, conversions, leads, customer_lifespan_months)
        ):
            raise ValueError("financial and count inputs must be non-negative")
        snapshot = ROISnapshot(platform)
        if cost > 0:
            snapshot.roi = (revenue - cost) / cost
            snapshot.roas = revenue / cost
        if conversions:
            snapshot.cpa = cost / conversions
        if impressions:
            snapshot.cpm = cost / impressions * 1000
        if clicks:
            snapshot.cpc = cost / clicks
        if leads:
            snapshot.cpl = cost / leads
        if revenue:
            snapshot.profit_margin = (revenue - cost) / revenue
        if monthly_revenue_per_customer:
            snapshot.ltv = monthly_revenue_per_customer * customer_lifespan_months
        self._snapshots.append(snapshot)
        if len(self._snapshots) > self._max_snapshots:
            del self._snapshots[:-self._max_snapshots]
        return snapshot

    def calculate_batch(self, items: List[Dict[str, Any]]) -> List[ROISnapshot]:
        return [self.calculate(platform=item.get("platform", ""), revenue=item.get("revenue", 0.0),
                               cost=item.get("cost", 0.0), impressions=item.get("impressions", 0),
                               clicks=item.get("clicks", 0), conversions=item.get("conversions", 0),
                               leads=item.get("leads", 0)) for item in items]

    def compare_platforms(self) -> List[Dict[str, Any]]:
        grouped: Dict[str, List[ROISnapshot]] = {}
        for snapshot in self._snapshots:
            grouped.setdefault(snapshot.platform, []).append(snapshot)
        return sorted(
            [{"platform": platform,
              "avg_roi": round(sum(s.roi for s in snapshots) / len(snapshots), 4),
              "snapshots": len(snapshots)} for platform, snapshots in grouped.items()],
            key=lambda item: item["avg_roi"], reverse=True,
        )

    def get_trend(self, platform: str = "") -> List[Dict[str, Any]]:
        snapshots = self._snapshots if not platform else [
            s for s in self._snapshots if s.platform == platform
        ]
        return [{"roi": s.roi, "roas": s.roas, "timestamp": s.calculated_at} for s in snapshots]

    def get_latest(self, platform: str = "") -> ROISnapshot:
        snapshots = self._snapshots if not platform else [
            s for s in self._snapshots if s.platform == platform
        ]
        return snapshots[-1] if snapshots else None

    def get_stats(self) -> Dict[str, Any]:
        avg = sum(s.roi for s in self._snapshots) / len(self._snapshots) if self._snapshots else 0.0
        return {"total_snapshots": len(self._snapshots), "avg_roi": round(avg, 4)}
