"""Tests for Phase 5 — Monitoring (10 modules)."""
from __future__ import annotations
import time
import pytest

from layers.layer18_monitoring.modules.metrics_engine.metrics_engine import MetricsEngine, MetricType
class TestMetricsEngine:
    def setup_method(self):
        self.me = MetricsEngine()
    def test_increment(self):
        self.me.increment("requests")
        self.me.increment("requests", 5)
        assert self.me.get_counter("requests") == 6
    def test_gauge(self):
        self.me.gauge_set("temperature", 36.5)
        assert self.me.get_gauge("temperature") == 36.5
    def test_histogram(self):
        for v in [10, 20, 30, 40, 50]:
            self.me.histogram_observe("latency", v)
        stats = self.me.get_histogram("latency")
        assert stats["count"] == 5
        assert stats["avg"] == 30.0
    def test_reset(self):
        self.me.increment("a")
        self.me.reset()
        assert self.me.get_counter("a") == 0.0
    def test_summary(self):
        self.me.increment("req")
        s = self.me.summary()
        assert s["counters"]["req"] == 1.0

from layers.layer18_monitoring.modules.profiler.profiler import Profiler
class TestProfiler:
    def setup_method(self):
        self.p = Profiler()
    def test_start_stop(self):
        self.p.start("test")
        time.sleep(0.01)
        ms = self.p.stop("test")
        assert ms > 0
    def test_decorator(self):
        @self.p.profile
        def func():
            return 42
        assert func() == 42
        assert self.p.get_profile("func") is not None
    def test_summary(self):
        self.p.start("a")
        self.p.stop("a")
        s = self.p.summary()
        assert s["functions"] == 1

from layers.layer18_monitoring.modules.tracer.tracer import Tracer, SpanStatus
class TestTracer:
    def setup_method(self):
        self.tracer = Tracer()
    def test_start_trace(self):
        span = self.tracer.start_trace("request")
        assert span.trace_id is not None
        assert span.span_id is not None
    def test_child_span(self):
        parent = self.tracer.start_trace("request")
        child = self.tracer.start_span(parent.trace_id, "db_query", parent_id=parent.span_id)
        assert child is not None
        assert child.parent_id == parent.span_id
    def test_finish_span(self):
        span = self.tracer.start_trace("request")
        assert self.tracer.finish_span(span.span_id, SpanStatus.OK)
    def test_stats(self):
        self.tracer.start_trace("a")
        stats = self.tracer.stats()
        assert stats["traces"] == 1

from layers.layer18_monitoring.modules.health_monitor.health_monitor import HealthMonitor, HealthLevel
class TestHealthMonitor:
    def setup_method(self):
        self.hm = HealthMonitor()
    def test_register_check(self):
        self.hm.register("db", lambda: {"healthy": True})
        result = self.hm.check("db")
        assert result["status"] == HealthLevel.HEALTHY.value
    def test_check_all(self):
        self.hm.register("a", lambda: {"healthy": True})
        self.hm.register("b", lambda: {"healthy": True})
        result = self.hm.check_all()
        assert result["overall"] == HealthLevel.HEALTHY.value
    def test_unhealthy(self):
        self.hm.register("bad", lambda: (_ for _ in ()).throw(Exception("fail")), max_failures=1)
        result = self.hm.check("bad")
        assert result["status"] == HealthLevel.UNHEALTHY.value
    def test_unregister(self):
        self.hm.register("x", lambda: {"healthy": True})
        assert self.hm.unregister("x")

from layers.layer18_monitoring.modules.alert_manager.alert_manager import AlertManager, AlertSeverity, AlertState
class TestAlertManager:
    def setup_method(self):
        self.am = AlertManager()
    def test_add_rule(self):
        rule = self.am.add_rule("high_cpu", lambda ctx: ctx.get("cpu", 0) > 90, AlertSeverity.CRITICAL)
        assert rule.name == "high_cpu"
    def test_evaluate_fire(self):
        self.am.add_rule("high_cpu", lambda ctx: ctx.get("cpu", 0) > 90, AlertSeverity.CRITICAL, "CPU too high")
        alerts = self.am.evaluate({"cpu": 95})
        assert len(alerts) == 1
        assert alerts[0].severity == AlertSeverity.CRITICAL
    def test_evaluate_no_fire(self):
        self.am.add_rule("high_cpu", lambda ctx: ctx.get("cpu", 0) > 90)
        alerts = self.am.evaluate({"cpu": 50})
        assert len(alerts) == 0
    def test_resolve(self):
        self.am.add_rule("test", lambda ctx: True)
        alerts = self.am.evaluate({})
        assert self.am.resolve_alert(alerts[0].alert_id)

from layers.layer18_monitoring.modules.error_tracker.error_tracker import ErrorTracker, ErrorSeverity
class TestErrorTracker:
    def setup_method(self):
        self.et = ErrorTracker()
    def test_track(self):
        entry = self.et.track("ValueError", "bad value", ErrorSeverity.HIGH)
        assert entry.error_type == "ValueError"
    def test_dedup(self):
        self.et.track("ValueError", "same error")
        self.et.track("ValueError", "same error")
        assert self.et.list_errors()[0]["count"] == 2
    def test_top_errors(self):
        for _ in range(5):
            self.et.track("A", "error_a")
        for _ in range(3):
            self.et.track("B", "error_b")
        top = self.et.get_top_errors(1)
        assert top[0]["type"] == "A"

from layers.layer18_monitoring.modules.performance_analyzer.performance_analyzer import PerformanceAnalyzer
class TestPerformanceAnalyzer:
    def setup_method(self):
        self.pa = PerformanceAnalyzer()
    def test_analyze(self):
        snap = self.pa.analyze({"cpu": 0.8, "memory": 0.6, "disk": 0.3})
        assert snap.grade in ["A+", "A", "B", "C", "D", "F"]
    def test_violations(self):
        self.pa.set_threshold("cpu", 0.0, 0.9)
        violations = self.pa.check_violations({"cpu": 0.95})
        assert len(violations) == 1

from layers.layer18_monitoring.modules.usage_analytics.usage_analytics import UsageAnalytics
class TestUsageAnalytics:
    def setup_method(self):
        self.ua = UsageAnalytics()
    def test_track(self):
        self.ua.track("api_call", user_id="u1", resource="content")
        assert self.ua.get_counts()["api_call"] == 1
    def test_top_users(self):
        for _ in range(5):
            self.ua.track("call", user_id="u1")
        for _ in range(3):
            self.ua.track("call", user_id="u2")
        top = self.ua.get_top_users(1)
        assert top[0]["user_id"] == "u1"

from layers.layer18_monitoring.modules.resource_monitor.resource_monitor import ResourceMonitor
class TestResourceMonitor:
    def setup_method(self):
        self.rm = ResourceMonitor()
    def test_collect(self):
        snap = self.rm.collect()
        assert snap.timestamp > 0
    def test_history(self):
        self.rm.collect()
        self.rm.collect()
        assert len(self.rm.get_history()) == 2

from layers.layer18_monitoring.modules.dashboard_backend.dashboard_backend import DashboardBackend
class TestDashboardBackend:
    def setup_method(self):
        self.db = DashboardBackend()
    def test_add_panel(self):
        panel = self.db.add_panel("p1", "Requests")
        assert panel.title == "Requests"
    def test_update_data(self):
        self.db.add_panel("p1", "Requests")
        assert self.db.update_panel_data("p1", {"values": [1, 2, 3]})
    def test_dashboard(self):
        self.db.add_panel("p1", "A")
        self.db.add_panel("p2", "B")
        dash = self.db.get_dashboard()
        assert dash["panel_count"] == 2
