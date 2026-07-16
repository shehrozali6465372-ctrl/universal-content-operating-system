"""Analytics Manager — Orchestrate the full analytics pipeline."""
from __future__ import annotations
import itertools
import time
from typing import Any, Callable, Dict, List, Optional

from layers.layer07_publishing.modules.analytics_hook.metrics_collector import MetricsCollector
from layers.layer07_publishing.modules.analytics_hook.metrics_normalizer import MetricsNormalizer
from layers.layer07_publishing.modules.analytics_hook.engagement_analyzer import EngagementAnalyzer
from layers.layer07_publishing.modules.analytics_hook.reach_analyzer import ReachAnalyzer
from layers.layer07_publishing.modules.analytics_hook.conversion_tracker import ConversionTracker
from layers.layer07_publishing.modules.analytics_hook.trend_tracker import TrendTracker
from layers.layer07_publishing.modules.analytics_hook.analytics_memory import AnalyticsMemory
from layers.layer07_publishing.modules.analytics_hook.performance_scorer import PerformanceScorer

_MANAGER_COUNTER = itertools.count(1)


class AnalyticsReport:
    """Unified analytics report for a single post."""

    __slots__ = (
        "report_id", "platform", "post_id", "engagement",
        "reach", "conversion", "trend", "performance",
        "timestamp",
    )

    def __init__(self, platform: str = "", post_id: str = "") -> None:
        self.report_id: str = f"arpt_{next(_MANAGER_COUNTER)}"
        self.platform = platform
        self.post_id = post_id
        self.engagement: Dict[str, Any] = {}
        self.reach: Dict[str, Any] = {}
        self.conversion: Dict[str, Any] = {}
        self.trend: Dict[str, Any] = {}
        self.performance: Dict[str, Any] = {}
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "platform": self.platform,
            "post_id": self.post_id,
            "engagement": self.engagement,
            "reach": self.reach,
            "conversion": self.conversion,
            "trend": self.trend,
            "performance": self.performance,
            "timestamp": self.timestamp,
        }


class AnalyticsManager:
    """Orchestrate the full analytics pipeline.

    Flow: Collect → Normalize → Analyze → Score → Store → Report
    """

    def __init__(
        self,
        collector: Optional[MetricsCollector] = None,
        normalizer: Optional[MetricsNormalizer] = None,
        engagement: Optional[EngagementAnalyzer] = None,
        reach: Optional[ReachAnalyzer] = None,
        conversion: Optional[ConversionTracker] = None,
        trend: Optional[TrendTracker] = None,
        memory: Optional[AnalyticsMemory] = None,
        scorer: Optional[PerformanceScorer] = None,
    ) -> None:
        self.collector = collector or MetricsCollector()
        self.normalizer = normalizer or MetricsNormalizer()
        self.engagement = engagement or EngagementAnalyzer()
        self.reach = reach or ReachAnalyzer()
        self.conversion = conversion or ConversionTracker()
        self.trend = trend or TrendTracker()
        self.memory = memory or AnalyticsMemory()
        self.scorer = scorer or PerformanceScorer()
        self._reports: List[AnalyticsReport] = []
        self._events: List[Dict[str, Any]] = []

    def analyze_post(
        self,
        platform: str,
        post_id: str,
        fetcher: Callable[[str, str], Dict[str, Any]],
    ) -> Optional[AnalyticsReport]:
        """Full pipeline: collect → normalize → analyze → score → store → report."""
        event = self.collector.collect_single(platform, post_id, fetcher)
        if not event:
            return None

        event = self.normalizer.normalize(event)
        self.trend.record(post_id, event.get("likes", 0) + event.get("comments", 0) + event.get("shares", 0))
        self.memory.store(event)

        report = AnalyticsReport(platform=platform, post_id=post_id)
        report.engagement = self.engagement.analyze(event).to_dict()
        report.reach = self.reach.analyze(event).to_dict()
        report.conversion = self.conversion.track(event).to_dict()
        report.trend = self.trend.analyze(post_id).to_dict()
        report.performance = self.scorer.score_event(event).to_dict()

        self._reports.append(report)
        self._events.append({
            "event": "analytics_collected",
            "platform": platform,
            "post_id": post_id,
            "report_id": report.report_id,
        })
        return report

    def get_reports(self, platform: Optional[str] = None) -> List[AnalyticsReport]:
        if platform:
            return [r for r in self._reports if r.platform == platform]
        return list(self._reports)

    def get_learning_signals(self) -> Dict[str, Any]:
        """Generate learning signals for Layer 9."""
        if not self._reports:
            return {"available": False}
        avg_engagement = sum(
            r.engagement.get("engagement_rate", 0) for r in self._reports
        ) / max(1, len(self._reports))
        return {
            "available": True,
            "report_count": len(self._reports),
            "avg_engagement_rate": round(avg_engagement, 3),
            "platforms": list(set(r.platform for r in self._reports)),
        }

    @property
    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)

    @property
    def report_count(self) -> int:
        return len(self._reports)
