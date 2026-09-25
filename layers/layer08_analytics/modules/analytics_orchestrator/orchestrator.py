"""Analytics orchestration with explicit durable-persistence boundaries."""
from __future__ import annotations
import time
import uuid
from threading import RLock
from typing import Any, Dict, List, Optional

from layers.layer08_analytics.modules.data_collector.collector import DataCollector, DataPoint
from layers.layer08_analytics.modules.metric_engine.metrics import MetricEngine
from layers.layer08_analytics.modules.report_generator.reports import ReportGenerator
from layers.layer08_analytics.modules.performance_analyzer.analyzer import PerformanceAnalyzer
from layers.layer08_analytics.modules.trend_detector.detector import TrendDetector
from layers.layer08_analytics.modules.ab_test_engine.engine import ABTestEngine
from layers.layer08_analytics.modules.funnel_analyzer.analyzer import FunnelAnalyzer
from layers.layer08_analytics.modules.attribution_engine.attribution import AttributionEngine
from layers.layer08_analytics.modules.dashboard_service.dashboard import DashboardService
from layers.layer08_analytics.modules.analytics_persistence import AnalyticsPersistence
from layers.layer08_analytics.modules.exceptions import DataCollectionError


class AnalyticsResult:
    __slots__ = ("pipeline_id", "data_points_collected", "metrics_calculated", "trends_detected",
                 "report_generated", "duration_ms", "insights", "timestamp", "persisted")
    def __init__(self) -> None:
        self.pipeline_id = f"ap_{uuid.uuid4().hex}"
        self.data_points_collected = self.metrics_calculated = self.trends_detected = 0
        self.report_generated = False; self.duration_ms = 0.0; self.insights: List[str] = []
        self.timestamp = time.time(); self.persisted = False
    def to_dict(self) -> Dict[str, Any]:
        return {"pipeline_id": self.pipeline_id, "data_points_collected": self.data_points_collected,
                "metrics_calculated": self.metrics_calculated, "trends_detected": self.trends_detected,
                "report_generated": self.report_generated, "duration_ms": round(self.duration_ms, 2),
                "insight_count": len(self.insights), "persisted": self.persisted}


class AnalyticsOrchestrator:
    """Collect -> calculate -> trend -> report, without creating Layer 13 resources."""

    def __init__(self, persistence: Optional[AnalyticsPersistence] = None, production: bool = False) -> None:
        if production and not (persistence is not None and bool(getattr(persistence, "durable", False))):
            raise RuntimeError("Layer 8 production mode requires a durable Layer 13 analytics persistence adapter")
        self.persistence = persistence
        persist = self._persist_point if persistence is not None else None
        self.collector = DataCollector(persist=persist)
        self.metric_engine = MetricEngine()
        self.report_generator = ReportGenerator()
        self.performance_analyzer = PerformanceAnalyzer()
        self.trend_detector = TrendDetector()
        self.ab_test_engine = ABTestEngine()
        self.funnel_analyzer = FunnelAnalyzer()
        self.attribution_engine = AttributionEngine()
        self.dashboard_service = DashboardService()
        self._pipeline_runs: List[AnalyticsResult] = []; self._events: List[Dict[str, Any]] = []
        self._lock = RLock()

    def _persist_point(self, point: DataPoint) -> None:
        if self.persistence is None: return
        self.persistence.record_metric(point.metric_name, point.value, {
            "source": point.source, "timestamp": point.timestamp, **point.dimensions
        })

    def run_pipeline(self, collect: bool = True, calculate: bool = True,
                     detect_trends: bool = True) -> AnalyticsResult:
        start = time.monotonic(); result = AnalyticsResult(); points: List[DataPoint] = []
        if collect:
            points = self.collector.collect_all()
            result.data_points_collected = len(points)
            for point in points:
                self.trend_detector.add_datapoint(point.metric_name, point.value)
        if calculate:
            result.metrics_calculated = len(self.metric_engine.get_all_definitions())
        if detect_trends:
            for metric_name in self.trend_detector.get_all_metrics():
                if self.trend_detector.detect(metric_name) is not None:
                    result.trends_detected += 1
        if points:
            totals: Dict[str, float] = {}
            for point in points:
                totals[point.metric_name] = totals.get(point.metric_name, 0.0) + point.value
            self.report_generator.generate_summary_report(result.pipeline_id, totals)
            result.report_generated = True
        result.duration_ms = (time.monotonic() - start) * 1000
        result.insights = self._generate_insights(result)
        with self._lock:
            self._pipeline_runs.append(result)
            self._events.append({"event": "pipeline_run", "pipeline_id": result.pipeline_id, "timestamp": result.timestamp})
        result.persisted = self.persistence is not None and bool(getattr(self.persistence, "durable", False))
        return result

    def diagnose_performance(self, points: List[Any], account_id: str = "", platform: str = "", niche: str = "") -> Dict[str, Any]:
        raw: Dict[str, float] = {}; provenance: List[Dict[str, Any]] = []
        for point in points or []:
            name = str(getattr(point, "metric_name", "") or "").strip().lower()
            value = getattr(point, "value", None)
            if not name or isinstance(value, bool) or not isinstance(value, (int, float)): continue
            raw[name] = float(value)
            provenance.append({"source": getattr(point, "source", ""), "metric": name,
                               "timestamp": getattr(point, "timestamp", 0.0),
                               "dimensions": dict(getattr(point, "dimensions", {}) or {})})
        normalized = dict(raw)
        if raw.get("reach", 0) > 0 and "clicks" in raw: normalized["click_through_rate"] = raw["clicks"] / raw["reach"]
        if raw.get("reach", 0) > 0 and "engagements" in raw: normalized["engagement_rate"] = raw["engagements"] / raw["reach"]
        findings: List[str] = []
        if raw.get("reach", 0) > 0 and raw.get("clicks", 0) <= 0: findings.append("reach_without_clicks")
        elif "clicks" in raw and normalized.get("click_through_rate", 1.0) < 0.01: findings.append("low_click_through_rate")
        if raw.get("reach", 0) > 0 and raw.get("engagements", 0) <= 0: findings.append("low_measurable_engagement")
        return {"available": bool(raw), "account_id": str(account_id).strip(), "platform": str(platform).strip(),
                "niche": str(niche).strip(), "raw_metrics": raw, "normalized_metrics": normalized,
                "diagnosis": findings, "provenance": provenance}

    def get_health(self) -> Dict[str, Any]:
        return {"pipeline_runs": len(self._pipeline_runs), "data_sources": len(self.collector.get_sources()),
                "total_data_points": self.collector.total_points, "metrics_defined": len(self.metric_engine.get_all_definitions()),
                "trends_tracked": len(self.trend_detector.get_all_metrics()), "ab_tests": len(self.ab_test_engine.get_all_tests()),
                "funnels": len(self.funnel_analyzer.get_all_funnels()), "durable_persistence": bool(self.persistence and getattr(self.persistence, "durable", False))}

    def _generate_insights(self, result: AnalyticsResult) -> List[str]:
        insights: List[str] = []
        if result.data_points_collected: insights.append(f"Collected {result.data_points_collected} data points")
        if result.trends_detected: insights.append(f"Detected {result.trends_detected} trends")
        if result.metrics_calculated: insights.append(f"Calculated {result.metrics_calculated} metrics")
        return insights
    @property
    def pipeline_run_count(self) -> int:
        with self._lock: return len(self._pipeline_runs)
    @property
    def events(self) -> List[Dict[str, Any]]:
        with self._lock: return list(self._events)
