"""MonitoringManager — Enterprise Monitoring & Observability manager.

Integrates:
- SystemMonitor (CPU, RAM, disk)
- APILatencyTracker (request timing)
- ErrorTracker (error classification)
- HealthDashboard (health scores)
- AlertManager (threshold-based alerts)
"""
from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timezone

from layers.layer18_monitoring.modules.monitoring_engine.system_monitor import SystemMonitor
from layers.layer18_monitoring.modules.monitoring_engine.api_latency_tracker import APILatencyTracker
from layers.layer18_monitoring.modules.monitoring_engine.error_tracker import ErrorTracker
from layers.layer18_monitoring.modules.monitoring_engine.health_dashboard import HealthDashboard
from layers.layer18_monitoring.modules.alert_manager.alert_manager import AlertManager, AlertSeverity


class MonitoringManager:
    """Main Monitoring & Observability manager."""

    def __init__(self):
        self._initialized = False

        # Components
        self.system: SystemMonitor = SystemMonitor()
        self.api_latency: APILatencyTracker = APILatencyTracker()
        self.errors: ErrorTracker = ErrorTracker()
        self.health: HealthDashboard = HealthDashboard()
        self.alerts: AlertManager = AlertManager()

    def initialize(self) -> bool:
        """Initialize monitoring system."""
        if self._initialized:
            return True

        # Setup default alert rules
        self._setup_default_alerts()

        # Initial health check
        self._update_health_from_system()

        self._initialized = True
        return True

    def _setup_default_alerts(self) -> None:
        """Setup default monitoring alert rules."""
        self.alerts.add_rule(
            "high_cpu",
            lambda ctx: ctx.get("cpu_percent", 0) > 90,
            AlertSeverity.WARNING,
            "CPU usage above 90%",
        )
        self.alerts.add_rule(
            "high_memory",
            lambda ctx: ctx.get("memory_percent", 0) > 85,
            AlertSeverity.WARNING,
            "Memory usage above 85%",
        )
        self.alerts.add_rule(
            "high_error_rate",
            lambda ctx: ctx.get("error_rate_pct", 0) > 5,
            AlertSeverity.ERROR,
            "Error rate above 5%",
        )

    def _update_health_from_system(self) -> None:
        """Update health dashboard from system metrics."""
        snap = self.system.snapshot()
        cpu = snap.get("cpu", {}).get("percent", 0)
        memory = snap.get("memory", {}).get("percent", 0)
        disk = snap.get("disk", {}).get("percent_used", 0)

        # System health
        sys_score = 100
        if cpu > 90: sys_score -= 30
        elif cpu > 70: sys_score -= 10
        if memory > 90: sys_score -= 30
        elif memory > 75: sys_score -= 10
        if disk > 95: sys_score -= 30
        elif disk > 80: sys_score -= 10

        status = "healthy" if sys_score >= 80 else "degraded" if sys_score >= 50 else "unhealthy"
        self.health.update_component("system", sys_score, status, {
            "cpu_percent": cpu, "memory_percent": memory, "disk_percent": disk,
        })

    def record_api_request(self, endpoint: str, latency_ms: float,
                           status_code: int = 200) -> None:
        """Record an API request."""
        self.api_latency.record(endpoint, latency_ms, status_code)

    def record_error(self, error_type: str, message: str,
                     module: str = "unknown") -> None:
        """Record an error."""
        self.errors.record(error_type, message, module)

    def evaluate_alerts(self) -> List[Dict[str, Any]]:
        """Evaluate all alert rules."""
        # Build context from current metrics
        snap = self.system.get_current()
        error_rate = self.errors.get_error_rate(300)

        context = {
            "cpu_percent": snap.get("cpu", {}).get("percent", 0),
            "memory_percent": snap.get("memory", {}).get("percent", 0),
            "disk_percent": snap.get("disk", {}).get("percent_used", 0),
            "error_rate_pct": error_rate.get("error_rate_per_minute", 0),
        }

        fired = self.alerts.evaluate(context)
        return [a.to_dict() for a in fired]

    def run_health_check(self) -> Dict[str, Any]:
        """Run a full health check."""
        # System
        self._update_health_from_system()

        # API latency
        api_stats = self.api_latency.stats()
        api_score = 100
        if api_stats.get("error_rate_pct", 0) > 10: api_score -= 30
        elif api_stats.get("error_rate_pct", 0) > 5: api_score -= 15
        if api_stats.get("avg_latency_ms", 0) > 1000: api_score -= 20
        api_status = "healthy" if api_score >= 80 else "degraded" if api_score >= 50 else "unhealthy"
        self.health.update_component("api", api_score, api_status, api_stats)

        # Errors
        error_stats = self.errors.stats()
        error_score = 100
        if error_stats.get("total_errors", 0) > 100: error_score -= 30
        elif error_stats.get("total_errors", 0) > 20: error_score -= 10
        error_status = "healthy" if error_score >= 80 else "degraded" if error_score >= 50 else "unhealthy"
        self.health.update_component("errors", error_score, error_status, error_stats)

        # Evaluate alerts
        alerts = self.evaluate_alerts()

        return self.health.get_overall_health()

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get comprehensive monitoring status — for --monitoring-status command."""
        # Run health check
        health = self.run_health_check()

        # Get all metrics
        system = self.system.get_current()
        api_stats = self.api_latency.stats()
        error_stats = self.errors.stats()
        health_stats = self.health.stats()
        alert_stats = self.alerts.stats()

        overall = "Healthy" if health.get("status") == "healthy" else "Degraded"

        return {
            "overall": overall,
            "initialized": self._initialized,
            "health": health,
            "system": system,
            "api": api_stats,
            "errors": error_stats,
            "health_dashboard": health_stats,
            "alerts": alert_stats,
        }

    def close(self):
        """Cleanup resources."""
        self._initialized = False


# Singleton
_monitoring_instance: Optional[MonitoringManager] = None


def get_monitoring() -> MonitoringManager:
    """Get or create Monitoring manager singleton."""
    global _monitoring_instance
    if _monitoring_instance is None:
        _monitoring_instance = MonitoringManager()
        _monitoring_instance.initialize()
    return _monitoring_instance
