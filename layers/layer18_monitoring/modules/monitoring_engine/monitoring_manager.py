"""Integrated monitoring manager with correct error-rate semantics."""
from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from layers.layer18_monitoring.modules.alert_manager.alert_manager import AlertManager, AlertSeverity
from layers.layer18_monitoring.modules.monitoring_engine.api_latency_tracker import APILatencyTracker
from layers.layer18_monitoring.modules.monitoring_engine.error_tracker import ErrorTracker
from layers.layer18_monitoring.modules.monitoring_engine.health_dashboard import HealthDashboard
from layers.layer18_monitoring.modules.monitoring_engine.system_monitor import SystemMonitor


class MonitoringManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._initialized = False
        self.system = SystemMonitor()
        self.api_latency = APILatencyTracker()
        self.errors = ErrorTracker()
        self.health = HealthDashboard()
        self.alerts = AlertManager()

    def initialize(self) -> bool:
        with self._lock:
            if self._initialized:
                return True
            self._setup_default_alerts()
            self._update_health_from_system()
            self._initialized = True
            return True

    def _setup_default_alerts(self) -> None:
        if self.alerts.list_rules():
            return
        self.alerts.add_rule("high_cpu", lambda ctx: ctx.get("cpu_percent", 0) > 90,
                             AlertSeverity.WARNING, "CPU usage above 90%")
        self.alerts.add_rule("high_memory", lambda ctx: ctx.get("memory_percent", 0) > 85,
                             AlertSeverity.WARNING, "Memory usage above 85%")
        self.alerts.add_rule("high_error_rate", lambda ctx: ctx.get("error_rate_pct", 0) > 5,
                             AlertSeverity.ERROR, "Error rate above 5%")

    def _update_health_from_system(self) -> None:
        snap = self.system.snapshot()
        cpu = snap["cpu"]["percent"]
        memory = snap["memory"]["percent"]
        disk = snap["disk"]["percent_used"]
        score = 100
        score -= 30 if cpu > 90 else 10 if cpu > 70 else 0
        score -= 30 if memory > 90 else 10 if memory > 75 else 0
        score -= 30 if disk > 95 else 10 if disk > 80 else 0
        status = "healthy" if score >= 80 else "degraded" if score >= 50 else "unhealthy"
        self.health.update_component("system", score, status,
                                     {"cpu_percent": cpu, "memory_percent": memory, "disk_percent": disk})

    def record_api_request(self, endpoint: str, latency_ms: float, status_code: int = 200) -> None:
        self.api_latency.record(endpoint, latency_ms, status_code)

    def record_error(self, error_type: str, message: str, module: str = "unknown") -> None:
        self.errors.record(error_type, message, module)

    def evaluate_alerts(self) -> List[Dict[str, Any]]:
        snap = self.system.get_current()
        error_rate = self.api_latency.get_error_rate(300)["error_rate_pct"]
        context = {"cpu_percent": snap["cpu"]["percent"], "memory_percent": snap["memory"]["percent"],
                   "disk_percent": snap["disk"]["percent_used"], "error_rate_pct": error_rate}
        return [alert.to_dict() for alert in self.alerts.evaluate(context)]

    def run_health_check(self) -> Dict[str, Any]:
        self._update_health_from_system()
        api_stats = self.api_latency.stats()
        api_score = 100 - (30 if api_stats["error_rate_pct"] > 10 else 15 if api_stats["error_rate_pct"] > 5 else 0)
        if api_stats["avg_latency_ms"] > 1000:
            api_score -= 20
        api_score = max(0, api_score)
        api_status = "healthy" if api_score >= 80 else "degraded" if api_score >= 50 else "unhealthy"
        self.health.update_component("api", api_score, api_status, api_stats)

        error_stats = self.errors.stats()
        error_score = 100 - (30 if error_stats["total_errors"] > 100 else 10 if error_stats["total_errors"] > 20 else 0)
        error_status = "healthy" if error_score >= 80 else "degraded" if error_score >= 50 else "unhealthy"
        self.health.update_component("errors", error_score, error_status, error_stats)
        self.evaluate_alerts()
        return self.health.get_overall_health()

    def get_monitoring_status(self) -> Dict[str, Any]:
        health = self.run_health_check()
        return {"overall": health["status"].title(), "initialized": self._initialized,
                "health": health, "system": self.system.get_current(),
                "api": self.api_latency.stats(), "errors": self.errors.stats(),
                "health_dashboard": self.health.stats(), "alerts": self.alerts.stats()}

    def close(self) -> None:
        with self._lock:
            self._initialized = False


_monitoring_instance: Optional[MonitoringManager] = None
_monitoring_lock = threading.Lock()


def get_monitoring() -> MonitoringManager:
    global _monitoring_instance
    with _monitoring_lock:
        if _monitoring_instance is None:
            _monitoring_instance = MonitoringManager()
            _monitoring_instance.initialize()
        return _monitoring_instance
