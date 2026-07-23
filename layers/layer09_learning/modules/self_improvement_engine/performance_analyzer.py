"""PerformanceAnalyzer — Analyzes KPIs: reach, CTR, RPM, revenue, engagement per post/account."""
from __future__ import annotations
import threading
import time
import uuid
from typing import Any, Dict, List, Optional


class PerformanceRecord:
    __slots__ = ("id", "entity_type", "entity_id", "platform", "niche",
                 "reach", "impressions", "clicks", "ctr", "engagement",
                 "engagement_rate", "revenue", "affiliate_revenue",
                 "rpm", "cost", "roi", "period", "timestamp", "metadata")

    def __init__(self, entity_type: str, entity_id: str, platform: str = "",
                 niche: str = "", period: str = "daily") -> None:
        self.id = str(uuid.uuid4())[:12]
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.platform = platform
        self.niche = niche
        self.reach = 0
        self.impressions = 0
        self.clicks = 0
        self.ctr = 0.0
        self.engagement = 0
        self.engagement_rate = 0.0
        self.revenue = 0.0
        self.affiliate_revenue = 0.0
        self.rpm = 0.0
        self.cost = 0.0
        self.roi = 0.0
        self.period = period
        self.timestamp = time.time()
        self.metadata: Dict[str, Any] = {}

    @property
    def performance_score(self) -> float:
        ctr_score = min(self.ctr / 5.0, 1.0) * 25
        eng_score = min(self.engagement_rate / 10.0, 1.0) * 25
        rev_score = min(self.revenue / 100, 1.0) * 30
        roi_score = min(max(self.roi, 0) / 300, 1.0) * 20
        return ctr_score + eng_score + rev_score + roi_score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "entity": self.entity_type, "entity_id": self.entity_id,
            "platform": self.platform, "niche": self.niche,
            "reach": self.reach, "impressions": self.impressions,
            "clicks": self.clicks, "ctr": round(self.ctr, 2),
            "engagement": self.engagement,
            "engagement_rate": round(self.engagement_rate, 2),
            "revenue": round(self.revenue, 2),
            "affiliate_revenue": round(self.affiliate_revenue, 2),
            "rpm": round(self.rpm, 2), "cost": round(self.cost, 2),
            "roi": round(self.roi, 2),
            "performance_score": round(self.performance_score, 1),
        }


class PerformanceBenchmark:
    __slots__ = ("metric", "p50", "p75", "p90", "p95", "mean", "std_dev", "count")

    def __init__(self, metric: str) -> None:
        self.metric = metric
        self.p50 = 0.0
        self.p75 = 0.0
        self.p90 = 0.0
        self.p95 = 0.0
        self.mean = 0.0
        self.std_dev = 0.0
        self.count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric": self.metric, "p50": round(self.p50, 2),
            "p75": round(self.p75, 2), "p90": round(self.p90, 2),
            "p95": round(self.p95, 2), "mean": round(self.mean, 2),
            "count": self.count,
        }


class PerformanceAnalyzer:
    """Analyzes performance KPIs across posts, accounts, platforms, and niches."""
    _instance: Optional["PerformanceAnalyzer"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "PerformanceAnalyzer":
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
        self._records: Dict[str, PerformanceRecord] = {}
        self._entity_index: Dict[str, List[str]] = {}
        self._platform_index: Dict[str, List[str]] = {}
        self._niche_index: Dict[str, List[str]] = {}
        self._benchmarks: Dict[str, PerformanceBenchmark] = {}

    def record(self, entity_type: str, entity_id: str, platform: str = "",
               niche: str = "", reach: int = 0, impressions: int = 0,
               clicks: int = 0, engagement: int = 0, revenue: float = 0.0,
               affiliate_revenue: float = 0.0, cost: float = 0.0,
               period: str = "daily") -> PerformanceRecord:
        rec = PerformanceRecord(entity_type, entity_id, platform, niche, period)
        rec.reach = reach
        rec.impressions = impressions
        rec.clicks = clicks
        rec.ctr = (clicks / impressions * 100) if impressions > 0 else 0
        rec.engagement = engagement
        rec.engagement_rate = (engagement / reach * 100) if reach > 0 else 0
        rec.revenue = revenue
        rec.affiliate_revenue = affiliate_revenue
        rec.rpm = (revenue / impressions * 1000) if impressions > 0 else 0
        rec.cost = cost
        rec.roi = ((revenue - cost) / cost * 100) if cost > 0 else 0
        self._records[rec.id] = rec
        self._entity_index.setdefault(f"{entity_type}:{entity_id}", []).append(rec.id)
        if platform:
            self._platform_index.setdefault(platform, []).append(rec.id)
        if niche:
            self._niche_index.setdefault(niche, []).append(rec.id)
        return rec

    def get_records(self, entity_type: str = "", entity_id: str = "",
                    platform: str = "", niche: str = "") -> List[PerformanceRecord]:
        if entity_type and entity_id:
            ids = self._entity_index.get(f"{entity_type}:{entity_id}", [])
            return [self._records[i] for i in ids if i in self._records]
        if platform:
            ids = self._platform_index.get(platform, [])
            return [self._records[i] for i in ids if i in self._records]
        if niche:
            ids = self._niche_index.get(niche, [])
            return [self._records[i] for i in ids if i in self._records]
        return list(self._records.values())

    def get_top_performers(self, entity_type: str = "", limit: int = 10,
                           metric: str = "performance_score") -> List[PerformanceRecord]:
        records = self.get_records(entity_type=entity_type)
        key_map = {
            "performance_score": lambda r: r.performance_score,
            "revenue": lambda r: r.revenue,
            "ctr": lambda r: r.ctr,
            "engagement": lambda r: r.engagement_rate,
            "roi": lambda r: r.roi,
            "rpm": lambda r: r.rpm,
        }
        fn = key_map.get(metric, key_map["performance_score"])
        return sorted(records, key=fn, reverse=True)[:limit]

    def get_underperformers(self, entity_type: str = "",
                            min_score: float = 30.0) -> List[PerformanceRecord]:
        records = self.get_records(entity_type=entity_type)
        return sorted(
            [r for r in records if r.performance_score < min_score],
            key=lambda r: r.performance_score,
        )

    def get_platform_summary(self) -> Dict[str, Dict[str, Any]]:
        summary: Dict[str, Dict[str, Any]] = {}
        for platform, ids in self._platform_index.items():
            records = [self._records[i] for i in ids if i in self._records]
            if not records:
                continue
            summary[platform] = {
                "count": len(records),
                "avg_ctr": round(sum(r.ctr for r in records) / len(records), 2),
                "avg_engagement": round(sum(r.engagement_rate for r in records) / len(records), 2),
                "total_revenue": round(sum(r.revenue for r in records), 2),
                "avg_roi": round(sum(r.roi for r in records) / len(records), 2),
                "avg_score": round(sum(r.performance_score for r in records) / len(records), 1),
            }
        return summary

    def get_niche_summary(self) -> Dict[str, Dict[str, Any]]:
        summary: Dict[str, Dict[str, Any]] = {}
        for niche, ids in self._niche_index.items():
            records = [self._records[i] for i in ids if i in self._records]
            if not records:
                continue
            summary[niche] = {
                "count": len(records),
                "total_revenue": round(sum(r.revenue for r in records), 2),
                "avg_score": round(sum(r.performance_score for r in records) / len(records), 1),
                "total_clicks": sum(r.clicks for r in records),
                "total_reach": sum(r.reach for r in records),
            }
        return summary

    def compute_benchmarks(self) -> Dict[str, PerformanceBenchmark]:
        metrics = {
            "ctr": [r.ctr for r in self._records.values()],
            "engagement_rate": [r.engagement_rate for r in self._records.values()],
            "revenue": [r.revenue for r in self._records.values()],
            "roi": [r.roi for r in self._records.values()],
            "performance_score": [r.performance_score for r in self._records.values()],
        }
        for metric_name, values in metrics.items():
            if not values:
                continue
            values_sorted = sorted(values)
            n = len(values_sorted)
            bm = PerformanceBenchmark(metric_name)
            bm.p50 = values_sorted[n // 2]
            bm.p75 = values_sorted[int(n * 0.75)]
            bm.p90 = values_sorted[int(n * 0.90)]
            bm.p95 = values_sorted[min(int(n * 0.95), n - 1)]
            bm.mean = sum(values) / n
            bm.count = n
            self._benchmarks[metric_name] = bm
        return self._benchmarks

    def get_analysis_report(self) -> Dict[str, Any]:
        records = list(self._records.values())
        return {
            "total_records": len(records),
            "platforms": len(self._platform_index),
            "niches": len(self._niche_index),
            "avg_performance_score": round(
                sum(r.performance_score for r in records) / len(records), 1
            ) if records else 0,
            "total_revenue": round(sum(r.revenue for r in records), 2),
            "total_affiliate_revenue": round(sum(r.affiliate_revenue for r in records), 2),
            "platform_summary": self.get_platform_summary(),
            "niche_summary": self.get_niche_summary(),
            "benchmarks": {k: v.to_dict() for k, v in self._benchmarks.items()},
            "top_10": [r.to_dict() for r in self.get_top_performers(limit=10)],
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "records": len(self._records),
            "platforms": len(self._platform_index),
            "niches": len(self._niche_index),
        }


def get_performance_analyzer() -> PerformanceAnalyzer:
    return PerformanceAnalyzer()
