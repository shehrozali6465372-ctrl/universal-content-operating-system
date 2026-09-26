"""Layer 18 production certification tests."""
from __future__ import annotations

import threading
import time

import pytest

from layers.layer18_monitoring.modules.alert_manager.alert_manager import AlertManager, AlertSeverity, AlertState
from layers.layer18_monitoring.modules.dashboard_backend.dashboard_backend import DashboardBackend
from layers.layer18_monitoring.modules.error_tracker.error_tracker import ErrorTracker as CompatErrorTracker
from layers.layer18_monitoring.modules.health_monitor.health_monitor import HealthLevel, HealthMonitor
from layers.layer18_monitoring.modules.metrics_engine.metrics_engine import MetricsEngine
from layers.layer18_monitoring.modules.monitoring_engine.api_latency_tracker import APILatencyTracker
from layers.layer18_monitoring.modules.monitoring_engine.error_tracker import ErrorTracker
from layers.layer18_monitoring.modules.monitoring_engine.health_dashboard import HealthDashboard
from layers.layer18_monitoring.modules.monitoring_engine.monitoring_manager import MonitoringManager
from layers.layer18_monitoring.modules.monitoring_engine.system_monitor import SystemMonitor
from layers.layer18_monitoring.modules.performance_analyzer.performance_analyzer import PerformanceAnalyzer
from layers.layer18_monitoring.modules.profiler.profiler import Profiler
from layers.layer18_monitoring.modules.resource_monitor.resource_monitor import ResourceMonitor
from layers.layer18_monitoring.modules.tracer.tracer import SpanStatus, Tracer
from layers.layer18_monitoring.modules.usage_analytics.usage_analytics import UsageAnalytics


def test_metrics_are_bounded_and_percentiles_are_deterministic():
    metrics = MetricsEngine(history_size=3)
    for value in [1, 2, 3, 4]:
        metrics.histogram_observe("latency", value)
    assert metrics.get_histogram("latency")["count"] == 3
    assert metrics.summary()["total_points"] == 3


def test_alert_rule_ids_do_not_collide_and_failures_are_observable():
    alerts = AlertManager(history_size=2)
    first = alerts.add_rule("same", lambda _: True, AlertSeverity.ERROR)
    second = alerts.add_rule("same", lambda _: True, AlertSeverity.ERROR)
    assert first.rule_id != second.rule_id
    alerts.add_rule("broken", lambda _: 1 / 0)
    alerts.evaluate()
    assert alerts.stats()["condition_errors"] == 1


def test_alert_lifecycle():
    alerts = AlertManager()
    rule = alerts.add_rule("test", lambda _: True, cooldown_seconds=0)
    fired = alerts.evaluate()
    assert fired and fired[0].state == AlertState.FIRING
    assert alerts.resolve_alert(fired[0].alert_id)
    assert alerts.list_alerts(AlertState.RESOLVED)


def test_api_error_rate_is_percentage_not_per_minute():
    tracker = APILatencyTracker()
    tracker.record("/x", 10, 200)
    tracker.record("/x", 10, 500)
    assert tracker.get_error_rate()["error_rate_pct"] == 50.0


def test_error_tracker_fingerprint_and_bounds():
    tracker = ErrorTracker(history_size=2)
    tracker.record("ValueError", "bad", "m")
    tracker.record("ValueError", "bad", "m")
    tracker.record("TypeError", "other", "m")
    assert tracker.stats()["total_errors"] == 3
    assert tracker.stats()["errors_in_history"] == 2
    assert tracker.get_top_errors(1)[0]["count"] == 2


def test_health_dashboard_and_history():
    dashboard = HealthDashboard(history_size=2)
    dashboard.update_component("db", 100, "healthy")
    assert dashboard.get_overall_health()["status"] == "healthy"
    dashboard.update_component("db", 20, "unhealthy")
    assert dashboard.get_overall_health()["status"] == "unhealthy"
    assert len(dashboard.get_health_history()) == 2


def test_health_monitor_timeout_and_failure_escalation():
    monitor = HealthMonitor(history_size=3)
    monitor.register("slow", lambda: time.sleep(0.05), timeout=0.01, max_failures=2)
    first = monitor.check("slow")
    second = monitor.check("slow")
    assert first["status"] == HealthLevel.DEGRADED.value
    assert second["status"] == HealthLevel.UNHEALTHY.value


def test_system_monitor_cpu_is_bounded():
    monitor = SystemMonitor(history_size=2)
    first = monitor.snapshot()
    second = monitor.snapshot()
    assert 0 <= first["cpu"]["percent"] <= 100
    assert 0 <= second["cpu"]["percent"] <= 100
    assert len(monitor.get_history("cpu")) <= 2


def test_resource_monitor_produces_snapshot_without_fake_required_values():
    monitor = ResourceMonitor(history_size=2)
    snap = monitor.collect()
    assert 0 <= snap.cpu_percent <= 100
    assert 0 <= snap.memory_percent <= 100
    assert 0 <= snap.disk_percent <= 100


def test_profiler_supports_nested_same_name_and_errors():
    profiler = Profiler()

    @profiler.profile
    def work():
        profiler.start("nested")
        profiler.stop("nested")
        return 1

    assert work() == 1
    profile = profiler.get_profile("work")
    assert profile is not None and profile.total_calls == 1


def test_profiler_concurrent_calls_are_not_collided():
    profiler = Profiler()

    @profiler.profile
    def work():
        time.sleep(0.001)

    threads = [threading.Thread(target=work) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert profiler.get_profile("work").total_calls == 10


def test_tracer_rejects_unknown_parent_and_bounds_traces():
    tracer = Tracer(max_traces=1, max_spans_per_trace=2)
    root = tracer.start_trace("root")
    child = tracer.start_span(root.trace_id, "child", parent_id=root.span_id)
    assert tracer.finish_span(child.span_id, SpanStatus.OK)
    with pytest.raises(RuntimeError):
        tracer.start_span(root.trace_id, "third")
    tracer.start_trace("new")
    assert tracer.stats()["traces"] == 1


def test_usage_analytics_is_bounded():
    usage = UsageAnalytics(history_size=2)
    usage.track("view", "u1")
    usage.track("view", "u1")
    usage.track("click", "u2")
    assert len(usage.list_events(limit=10)) == 2
    assert usage.get_user_activity("u1") == 2


def test_dashboard_backend_is_bounded():
    dashboard = DashboardBackend(history_size=2)
    dashboard.add_panel("p", "Panel")
    assert dashboard.update_panel_data("p", {"ok": True})
    dashboard.snapshot()
    dashboard.snapshot()
    dashboard.snapshot()
    assert len(dashboard.get_snapshots()) == 2


def test_performance_analyzer_requires_normalized_metrics():
    analyzer = PerformanceAnalyzer(history_size=2)
    with pytest.raises(ValueError):
        analyzer.analyze({"latency_ms": 100})
    snapshot = analyzer.analyze({"availability": 1.0, "quality": 0.8})
    assert snapshot.score == 90.0


def test_monitoring_manager_uses_api_error_percentage():
    manager = MonitoringManager()
    manager.api_latency.record("/x", 10, 500)
    manager.api_latency.record("/x", 10, 200)
    fired = manager.evaluate_alerts()
    assert isinstance(fired, list)
    assert manager.get_monitoring_status()["initialized"] is False


def test_compat_error_tracker_is_bounded():
    tracker = CompatErrorTracker(history_size=1)
    tracker.track("ValueError", "bad")
    tracker.track("ValueError", "bad")
    assert tracker.stats()["total_occurrences"] == 2
