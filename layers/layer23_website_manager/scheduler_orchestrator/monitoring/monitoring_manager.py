"""MonitoringManager — Track running jobs, queue status, worker stats."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.scheduler_orchestrator.models.scheduler_models import (
    ResourceMetrics,
)


class MonitoringManager:
    """Monitor scheduler health, resource usage, and execution status."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._metrics_history: List[ResourceMetrics] = []
        self._max_history: int = 1000
        self._alerts_enabled: bool = True
        self._alert_thresholds: Dict[str, float] = {
            "cpu_warning": 80.0,
            "cpu_critical": 95.0,
            "memory_warning_mb": 1024.0,
            "memory_critical_mb": 2048.0,
            "queue_critical": 1000,
            "failure_rate_warning": 20.0,
        }

    def record_metrics(self, metrics: ResourceMetrics) -> None:
        with self._lock:
            self._metrics_history.append(metrics)
            if len(self._metrics_history) > self._max_history:
                self._metrics_history = self._metrics_history[-self._max_history:]

    def get_latest_metrics(self) -> Optional[ResourceMetrics]:
        with self._lock:
            return self._metrics_history[-1] if self._metrics_history else None

    def get_metrics_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            return [m.to_dict() for m in self._metrics_history[-limit:]]

    def check_health(self, current_stats: Dict[str, Any]) -> Dict[str, Any]:
        health = {"status": "healthy", "issues": [], "warnings": []}
        latest = self.get_latest_metrics()
        if latest:
            if latest.cpu_percent > self._alert_thresholds["cpu_critical"]:
                health["issues"].append(f"CPU at {latest.cpu_percent}% (critical)")
                health["status"] = "critical"
            elif latest.cpu_percent > self._alert_thresholds["cpu_warning"]:
                health["warnings"].append(f"CPU at {latest.cpu_percent}% (warning)")
                if health["status"] == "healthy":
                    health["status"] = "warning"

            if latest.memory_mb > self._alert_thresholds["memory_critical_mb"]:
                health["issues"].append(f"Memory at {latest.memory_mb}MB (critical)")
                health["status"] = "critical"
            elif latest.memory_mb > self._alert_thresholds["memory_warning_mb"]:
                health["warnings"].append(f"Memory at {latest.memory_mb}MB (warning)")

        if current_stats.get("total", 0) > self._alert_thresholds["queue_critical"]:
            health["warnings"].append("Queue size critical")
            if health["status"] == "healthy":
                health["status"] = "warning"

        total = (current_stats.get("completed", 0) + current_stats.get("failed", 0))
        if total > 0:
            fail_rate = (current_stats.get("failed", 0) / total) * 100
            if fail_rate > self._alert_thresholds["failure_rate_warning"]:
                health["warnings"].append(f"Failure rate at {fail_rate:.1f}% (warning)")
                if health["status"] == "healthy":
                    health["status"] = "warning"

        return health

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "metrics_records": len(self._metrics_history),
                "alerts_enabled": self._alerts_enabled,
                "thresholds": self._alert_thresholds,
            }
