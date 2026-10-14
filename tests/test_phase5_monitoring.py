"""Tests for the retained metrics, health-check, and alert modules."""
from __future__ import annotations
from layers.layer18_monitoring.modules.metrics_engine.metrics_engine import MetricsEngine
from layers.layer18_monitoring.modules.health_monitor.health_monitor import HealthMonitor, HealthLevel
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

