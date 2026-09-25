"""Layer 8 production gate: correctness, failure semantics, persistence boundary, and pipeline flow."""
from __future__ import annotations

import pytest

from layers.layer08_analytics.modules.ab_test_engine.engine import ABTestEngine
from layers.layer08_analytics.modules.analytics_orchestrator.orchestrator import AnalyticsOrchestrator
from layers.layer08_analytics.modules.attribution_engine.attribution import AttributionEngine, AttributionTouchpoint
from layers.layer08_analytics.modules.data_collector.collector import DataCollector, DataSource
from layers.layer08_analytics.modules.funnel_analyzer.analyzer import FunnelAnalyzer
from layers.layer08_analytics.modules.metric_engine.metrics import MetricDefinition, MetricEngine
from layers.layer08_analytics.modules.report_generator.reports import ReportGenerator
from layers.layer08_analytics.modules.trend_detector.detector import TrendDetector
from layers.layer08_analytics.modules.analytics_persistence import PostgreSQLAnalyticsPersistence
from layers.layer13_persistence.modules.postgresql.manager import PostgreSQLManager


class Sink:
    durable = True
    def __init__(self) -> None:
        self.rows = []
    def record_metric(self, metric_name, value, dimensions):
        self.rows.append((metric_name, value, dimensions))
        return len(self.rows)


def test_collector_rejects_silent_source_failure():
    collector = DataCollector()
    collector.register_source(DataSource("broken", fetcher=lambda: (_ for _ in ()).throw(RuntimeError("boom"))))
    with pytest.raises(Exception):
        collector.collect("broken")


def test_collector_persists_before_retaining():
    sink = Sink()
    collector = DataCollector(persist=lambda point: sink.record_metric(point.metric_name, point.value, point.to_dict()["dimensions"]))
    point = collector.collect_manual("meta", "reach", 10, account_id="a1")
    assert collector.total_points == 1
    assert sink.rows[0][0] == "reach"
    assert sink.rows[0][2]["account_id"] == "a1"
    assert point.value == 10.0


def test_metric_aggregate_uses_requested_formula():
    engine = MetricEngine()
    engine.define(MetricDefinition("m", "Average", "avg"))
    result = engine.aggregate("m", [{"value": 2}, {"value": 4}])
    assert result.value == 3.0
    assert result.formula_used == "avg"


def test_metric_rejects_nan():
    engine = MetricEngine()
    engine.define(MetricDefinition("m"))
    with pytest.raises(Exception):
        engine.calculate("m", [float("nan")])


def test_trend_detect_all_does_not_duplicate_detection():
    detector = TrendDetector()
    detector.add_batch("reach", [1, 2, 3, 4])
    results = detector.detect_all()
    assert len(results) == 1
    assert detector.detection_count == 1


def test_ab_test_requires_real_exposure():
    engine = ABTestEngine()
    test = engine.create_test("t1", "test", ["control", "variant"])
    assert engine.record_impression("t1", test.variants[0].variant_id) is False
    assert engine.start_test("t1")
    assert engine.record_conversion("t1", test.variants[0].variant_id) is False
    assert engine.record_impression("t1", test.variants[0].variant_id)
    assert engine.record_conversion("t1", test.variants[0].variant_id)


def test_funnel_rejects_impossible_counts():
    analyzer = FunnelAnalyzer()
    analyzer.create_funnel("f1", "funnel", ["visit", "buy"])
    with pytest.raises(ValueError):
        analyzer.update_step("f1", "f1_s0", 10, 11)


def test_attribution_linear_conserves_revenue():
    engine = AttributionEngine()
    a = AttributionTouchpoint("facebook"); a.revenue = 100
    b = AttributionTouchpoint("google")
    engine.add_touchpoint("customer", a); engine.add_touchpoint("customer", b)
    results = engine.analyze_linear()
    assert sum(r.linear_revenue for r in results) == pytest.approx(100.0)


def test_report_ids_do_not_collide():
    generator = ReportGenerator()
    a = generator.generate_summary_report("a", {"reach": 1})
    b = generator.generate_summary_report("b", {"reach": 1})
    assert a.report_id != b.report_id


def test_orchestrator_uses_injected_persistence_and_generates_report():
    sink = Sink()
    orchestrator = AnalyticsOrchestrator(persistence=sink)
    orchestrator.collector.register_source(DataSource("src", fetcher=lambda: {"reach": 10}))
    result = orchestrator.run_pipeline()
    assert result.persisted is True
    assert result.report_generated is True
    assert sink.rows


def test_orchestrator_does_not_create_layer13_pool():
    orchestrator = AnalyticsOrchestrator()
    assert orchestrator.persistence is None
    assert orchestrator.get_health()["durable_persistence"] is False


def test_production_mode_fails_closed_without_durable_persistence():
    with pytest.raises(RuntimeError):
        AnalyticsOrchestrator(production=True)


def test_production_mode_accepts_durable_persistence():
    orchestrator = AnalyticsOrchestrator(persistence=Sink(), production=True)
    assert orchestrator.get_health()["durable_persistence"] is True


def test_real_postgresql_persistence_path():
    manager = PostgreSQLManager()
    assert manager.initialize() is True
    try:
        assert manager.analytics is not None
        persistence = PostgreSQLAnalyticsPersistence(manager.analytics)
        orchestrator = AnalyticsOrchestrator(persistence=persistence, production=True)
        metric = "layer8_certification_real_db"
        point = orchestrator.collector.collect_manual("ci", metric, 42.0, run_id="layer8-cert")
        assert point.value == 42.0
        rows = manager.analytics.get_latest(metric)
        assert rows is not None
        assert float(rows["metric_value"]) == 42.0
    finally:
        manager.close()
