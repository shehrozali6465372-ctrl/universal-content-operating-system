"""Analytics Orchestrator — Orchestrate the complete analytics pipeline."""
from __future__ import annotations
import time
from typing import Any, Dict, List

from layers.layer08_analytics.modules.data_collector.collector import DataCollector
from layers.layer08_analytics.modules.metric_engine.metrics import MetricEngine
from layers.layer08_analytics.modules.report_generator.reports import ReportGenerator
from layers.layer08_analytics.modules.performance_analyzer.analyzer import PerformanceAnalyzer
from layers.layer08_analytics.modules.trend_detector.detector import TrendDetector
from layers.layer08_analytics.modules.ab_test_engine.engine import ABTestEngine
from layers.layer08_analytics.modules.funnel_analyzer.analyzer import FunnelAnalyzer
from layers.layer08_analytics.modules.attribution_engine.attribution import AttributionEngine
from layers.layer08_analytics.modules.dashboard_service.dashboard import DashboardService


class AnalyticsResult:
    """Result of a complete analytics pipeline run."""

    __slots__ = ("pipeline_id", "data_points_collected", "metrics_calculated",
                 "trends_detected", "report_generated", "duration_ms",
                 "insights", "timestamp")

    def __init__(self) -> None:
        self.pipeline_id: str = f"ap_{int(time.time() * 1000) % 100000}"
        self.data_points_collected: int = 0
        self.metrics_calculated: int = 0
        self.trends_detected: int = 0
        self.report_generated: bool = False
        self.duration_ms: float = 0.0
        self.insights: List[str] = []
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "data_points_collected": self.data_points_collected,
            "metrics_calculated": self.metrics_calculated,
            "trends_detected": self.trends_detected,
            "report_generated": self.report_generated,
            "duration_ms": round(self.duration_ms, 2),
            "insight_count": len(self.insights),
        }


class AnalyticsOrchestrator:
    """Orchestrate the complete analytics pipeline.

    Flow: Collect → Calculate → Detect Trends → Analyze → Report → Dashboard
    """

    def __init__(self) -> None:
        self.collector = DataCollector()
        self.metric_engine = MetricEngine()
        self.report_generator = ReportGenerator()
        self.performance_analyzer = PerformanceAnalyzer()
        self.trend_detector = TrendDetector()
        self.ab_test_engine = ABTestEngine()
        self.funnel_analyzer = FunnelAnalyzer()
        self.attribution_engine = AttributionEngine()
        self.dashboard_service = DashboardService()
        self._pipeline_runs: List[AnalyticsResult] = []
        self._events: List[Dict[str, Any]] = []

    def run_pipeline(
        self,
        collect: bool = True,
        calculate: bool = True,
        detect_trends: bool = True,
    ) -> AnalyticsResult:
        start = time.time()
        result = AnalyticsResult()

        if collect:
            points = self.collector.collect_all()
            result.data_points_collected = len(points)

        if calculate:
            definitions = self.metric_engine.get_all_definitions()
            result.metrics_calculated = len(definitions)

        if detect_trends:
            for metric_name in self.trend_detector.get_all_metrics():
                trend = self.trend_detector.detect(metric_name)
                if trend:
                    result.trends_detected += 1

        result.duration_ms = (time.time() - start) * 1000
        result.insights = self._generate_insights(result)
        self._pipeline_runs.append(result)
        self._events.append({"event": "pipeline_run", "pipeline_id": result.pipeline_id})
        return result

    def get_health(self) -> Dict[str, Any]:
        return {
            "pipeline_runs": len(self._pipeline_runs),
            "data_sources": len(self.collector.get_sources()),
            "total_data_points": self.collector.total_points,
            "metrics_defined": len(self.metric_engine.get_all_definitions()),
            "trends_tracked": len(self.trend_detector.get_all_metrics()),
            "ab_tests": len(self.ab_test_engine.get_all_tests()),
            "funnels": len(self.funnel_analyzer.get_all_funnels()),
        }

    def _generate_insights(self, result: AnalyticsResult) -> List[str]:
        insights = []
        if result.data_points_collected > 0:
            insights.append(f"Collected {result.data_points_collected} data points")
        if result.trends_detected > 0:
            insights.append(f"Detected {result.trends_detected} trends")
        if result.metrics_calculated > 0:
            insights.append(f"Calculated {result.metrics_calculated} metrics")
        return insights

    @property
    def pipeline_run_count(self) -> int:
        return len(self._pipeline_runs)

    @property
    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)
