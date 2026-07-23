"""Tests for Monitoring & Observability Enterprise Features.

Covers:
- SystemMonitor (snapshot, trends, anomalies)
- APILatencyTracker (record, stats, slow endpoints, throughput)
- ErrorTracker (record, groups, trends, rates)
- HealthDashboard (component health, overall, trends)
- AlertManager (rules, evaluate, resolve)
- MonitoringManager (integration, status)
"""
from __future__ import annotations
import os
import sys
import time
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─── SystemMonitor Tests ─────────────────────────────────────────

class TestSystemMonitor:
    def setup_method(self):
        from layers.layer18_monitoring.modules.monitoring_engine.system_monitor import SystemMonitor
        self.monitor = SystemMonitor(history_size=100)

    def test_snapshot(self):
        snap = self.monitor.snapshot()
        assert "timestamp" in snap
        assert "cpu" in snap
        assert "memory" in snap
        assert "disk" in snap

    def test_cpu_info(self):
        snap = self.monitor.snapshot()
        cpu = snap["cpu"]
        assert "percent" in cpu
        assert "cores" in cpu
        assert cpu["cores"] >= 1

    def test_memory_info(self):
        snap = self.monitor.snapshot()
        mem = snap["memory"]
        assert "percent" in mem
        assert "total_mb" in mem
        assert mem["total_mb"] > 0

    def test_disk_info(self):
        snap = self.monitor.snapshot()
        disk = snap["disk"]
        assert "percent_used" in disk
        assert "total_gb" in disk
        assert disk["total_gb"] > 0

    def test_get_current(self):
        self.monitor.snapshot()
        current = self.monitor.get_current()
        assert "cpu" in current

    def test_trend(self):
        for _ in range(5):
            self.monitor.snapshot()
        trend = self.monitor.get_trend("cpu", window=5)
        assert "trend" in trend
        assert "values" in trend

    def test_anomalies(self):
        for _ in range(10):
            self.monitor.snapshot()
        anomalies = self.monitor.detect_anomalies("cpu")
        assert isinstance(anomalies, list)

    def test_history(self):
        for _ in range(3):
            self.monitor.snapshot()
        history = self.monitor.get_history()
        assert len(history) >= 3

    def test_set_threshold(self):
        self.monitor.set_threshold("cpu_warning", 80.0)
        assert self.monitor._thresholds["cpu_warning"] == 80.0

    def test_stats(self):
        self.monitor.snapshot()
        stats = self.monitor.stats()
        assert "cpu_history_size" in stats


# ─── APILatencyTracker Tests ────────────────────────────────────

class TestAPILatencyTracker:
    def setup_method(self):
        from layers.layer18_monitoring.modules.monitoring_engine.api_latency_tracker import APILatencyTracker
        self.tracker = APILatencyTracker()

    def test_record(self):
        self.tracker.record("/api/generate", 150.0, 200, "POST")
        stats = self.tracker.get_endpoint_stats("/api/generate")
        assert stats["requests"] == 1

    def test_multiple_records(self):
        for i in range(10):
            self.tracker.record("/api/generate", 100 + i * 10, 200)
        stats = self.tracker.get_endpoint_stats("/api/generate")
        assert stats["requests"] == 10
        assert stats["avg_ms"] > 0

    def test_percentiles(self):
        for i in range(100):
            self.tracker.record("/api/search", float(i), 200)
        stats = self.tracker.get_endpoint_stats("/api/search")
        assert stats["p50_ms"] <= stats["p95_ms"]
        assert stats["p95_ms"] <= stats["p99_ms"]

    def test_error_rate(self):
        self.tracker.record("/api/generate", 100, 200)
        self.tracker.record("/api/generate", 200, 500)
        error_rate = self.tracker.get_error_rate()
        assert error_rate["errors"] == 1
        assert error_rate["total"] == 2

    def test_slow_endpoints(self):
        self.tracker.record("/api/slow", 5000, 200)
        slow = self.tracker.get_slow_endpoints(threshold_ms=1000)
        assert len(slow) > 0

    def test_throughput(self):
        for _ in range(5):
            self.tracker.record("/api/test", 50, 200)
        throughput = self.tracker.get_throughput(window_seconds=60)
        assert throughput["requests_in_window"] == 5

    def test_get_all_stats(self):
        self.tracker.record("/api/a", 100, 200)
        self.tracker.record("/api/b", 200, 200)
        all_stats = self.tracker.get_all_stats()
        assert "/api/a" in all_stats
        assert "/api/b" in all_stats

    def test_stats(self):
        self.tracker.record("/api/test", 100, 200)
        stats = self.tracker.stats()
        assert stats["total_requests"] == 1


# ─── ErrorTracker Tests ──────────────────────────────────────────

class TestErrorTracker:
    def setup_method(self):
        from layers.layer18_monitoring.modules.monitoring_engine.error_tracker import ErrorTracker
        self.tracker = ErrorTracker()

    def test_record(self):
        error = self.tracker.record("ValueError", "Invalid input", "layer04")
        assert error["error_type"] == "ValueError"
        assert error["module"] == "layer04"

    def test_error_groups(self):
        for _ in range(5):
            self.tracker.record("TypeError", "Same error", "layer03")
        top = self.tracker.get_top_errors()
        assert len(top) == 1
        assert top[0]["count"] == 5

    def test_by_module(self):
        self.tracker.record("Error", "e1", "layer01")
        self.tracker.record("Error", "e2", "layer01")
        self.tracker.record("Error", "e3", "layer02")
        by_module = self.tracker.get_errors_by_module()
        assert by_module["layer01"] == 2

    def test_by_type(self):
        self.tracker.record("TypeError", "t1", "mod")
        self.tracker.record("ValueError", "v1", "mod")
        self.tracker.record("TypeError", "t2", "mod")
        by_type = self.tracker.get_errors_by_type()
        assert by_type["TypeError"] == 2

    def test_error_rate(self):
        for _ in range(10):
            self.tracker.record("Error", "msg", "mod")
        rate = self.tracker.get_error_rate(window_seconds=60)
        assert rate["error_count"] == 10

    def test_recent(self):
        self.tracker.record("Error", "e1", "mod1")
        self.tracker.record("Error", "e2", "mod2")
        recent = self.tracker.get_recent(limit=5, module="mod1")
        assert len(recent) == 1

    def test_trend(self):
        for _ in range(5):
            self.tracker.record("Error", "msg", "mod")
        trend = self.tracker.get_trend(window_hours=1)
        assert len(trend) == 1
        assert trend[0]["count"] == 5

    def test_clear(self):
        self.tracker.record("Error", "msg", "mod")
        self.tracker.clear()
        stats = self.tracker.stats()
        assert stats["total_errors"] == 0

    def test_stats(self):
        self.tracker.record("TypeError", "t", "mod")
        self.tracker.record("ValueError", "v", "mod")
        stats = self.tracker.stats()
        assert stats["total_errors"] == 2
        assert stats["unique_error_groups"] == 2


# ─── HealthDashboard Tests ──────────────────────────────────────

class TestHealthDashboard:
    def setup_method(self):
        from layers.layer18_monitoring.modules.monitoring_engine.health_dashboard import HealthDashboard
        self.dashboard = HealthDashboard()

    def test_update_component(self):
        self.dashboard.update_component("database", 95, "healthy")
        health = self.dashboard.get_component_health("database")
        assert health["score"] == 95
        assert health["status"] == "healthy"

    def test_overall_health(self):
        self.dashboard.update_component("db", 90, "healthy")
        self.dashboard.update_component("cache", 85, "healthy")
        overall = self.dashboard.get_overall_health()
        assert overall["score"] > 0
        assert overall["status"] == "healthy"

    def test_degraded_health(self):
        self.dashboard.update_component("db", 90, "healthy")
        self.dashboard.update_component("cache", 40, "degraded")
        overall = self.dashboard.get_overall_health()
        assert overall["status"] == "degraded"

    def test_unhealthy_component(self):
        self.dashboard.update_component("db", 20, "unhealthy")
        unhealthy = self.dashboard.get_unhealthy_components()
        assert len(unhealthy) == 1

    def test_health_history(self):
        self.dashboard.update_component("db", 90, "healthy")
        self.dashboard.get_overall_health()  # Records in history
        history = self.dashboard.get_health_history()
        assert len(history) >= 1

    def test_score_trend(self):
        for _ in range(5):
            self.dashboard.update_component("db", 80, "healthy")
            self.dashboard.get_overall_health()
        trend = self.dashboard.get_score_trend()
        assert "trend" in trend

    def test_stats(self):
        self.dashboard.update_component("db", 90, "healthy")
        stats = self.dashboard.stats()
        assert stats["total_components"] == 1
        assert stats["healthy"] == 1


# ─── AlertManager Tests ──────────────────────────────────────────

class TestAlertManager:
    def setup_method(self):
        from layers.layer18_monitoring.modules.alert_manager.alert_manager import AlertManager
        self.manager = AlertManager()

    def test_add_rule(self):
        rule = self.manager.add_rule("test_rule", lambda ctx: True)
        assert rule.name == "test_rule"

    def test_evaluate_fires(self):
        self.manager.add_rule("always_fire", lambda ctx: True, cooldown_seconds=0)
        fired = self.manager.evaluate({})
        assert len(fired) >= 1

    def test_evaluate_not_fired(self):
        self.manager.add_rule("never_fire", lambda ctx: False)
        fired = self.manager.evaluate({})
        assert len(fired) == 0

    def test_resolve_alert(self):
        self.manager.add_rule("fire", lambda ctx: True, cooldown_seconds=0)
        fired = self.manager.evaluate({})
        assert len(fired) > 0
        resolved = self.manager.resolve_alert(fired[0].alert_id)
        assert resolved is True

    def test_list_alerts(self):
        self.manager.add_rule("fire", lambda ctx: True, cooldown_seconds=0)
        self.manager.evaluate({})
        alerts = self.manager.list_alerts()
        assert len(alerts) >= 1

    def test_stats(self):
        self.manager.add_rule("test", lambda ctx: True, cooldown_seconds=0)
        self.manager.evaluate({})
        stats = self.manager.stats()
        assert stats["rules"] >= 1


# ─── MonitoringManager Integration Tests ─────────────────────────

class TestMonitoringManager:
    def setup_method(self):
        from layers.layer18_monitoring.modules.monitoring_engine.monitoring_manager import MonitoringManager
        self.mon = MonitoringManager()
        self.mon.initialize()

    def test_initialize(self):
        assert self.mon._initialized is True

    def test_record_api_request(self):
        self.mon.record_api_request("/api/generate", 150.0, 200)
        stats = self.mon.api_latency.stats()
        assert stats["total_requests"] == 1

    def test_record_error(self):
        self.mon.record_error("ValueError", "Bad input", "layer04")
        stats = self.mon.errors.stats()
        assert stats["total_errors"] == 1

    def test_evaluate_alerts(self):
        alerts = self.mon.evaluate_alerts()
        assert isinstance(alerts, list)

    def test_run_health_check(self):
        health = self.mon.run_health_check()
        assert "score" in health
        assert "status" in health
        assert "components" in health

    def test_get_monitoring_status(self):
        status = self.mon.get_monitoring_status()
        assert status["overall"] in ("Healthy", "Degraded")
        assert "health" in status
        assert "system" in status
        assert "api" in status
        assert "errors" in status
        assert "alerts" in status

    def test_full_enterprise_stack(self):
        """Test all monitoring components working together."""
        # Record API traffic
        for i in range(50):
            self.mon.record_api_request("/api/generate", 100 + i * 10, 200)
        for i in range(5):
            self.mon.record_api_request("/api/publish", 200, 500)

        # Record errors
        for _ in range(10):
            self.mon.record_error("TimeoutError", "Request timeout", "layer07")
        self.mon.record_error("ValueError", "Bad input", "layer04")

        # Run health check
        health = self.mon.run_health_check()
        assert health["score"] > 0

        # Get full status
        status = self.mon.get_monitoring_status()
        assert status["api"]["total_requests"] == 55
        assert status["errors"]["total_errors"] == 11

        # Check alerts
        alerts = self.mon.evaluate_alerts()
        assert isinstance(alerts, list)

        # Check system metrics
        assert "cpu" in status["system"]
        assert "memory" in status["system"]
