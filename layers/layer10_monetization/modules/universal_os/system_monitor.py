"""SystemMonitor — Track CPU, RAM, GPU, errors, latency, and health."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class SystemMonitor:
    """Monitor system health, errors, latency, and resource usage."""

    def __init__(self) -> None:
        self._metrics: Dict[str, List[Dict[str, Any]]] = {}
        self._alerts: List[Dict[str, Any]] = []
        self._error_log: List[Dict[str, Any]] = []

    def record_metric(self, metric_name: str, value: float,
                      tags: Dict[str, str] = None) -> None:
        if metric_name not in self._metrics:
            self._metrics[metric_name] = []
        self._metrics[metric_name].append({"value": value, "timestamp": time.time(),
                                            "tags": tags or {}})

    def record_error(self, source: str, error: str,
                     severity: str = "warning") -> None:
        self._error_log.append({"source": source, "error": error,
                                 "severity": severity, "timestamp": time.time()})
        if severity in ("error", "critical"):
            self._alerts.append({"source": source, "error": error,
                                  "severity": severity, "timestamp": time.time()})

    def get_metric(self, metric_name: str, count: int = 10) -> List[Dict[str, Any]]:
        return self._metrics.get(metric_name, [])[-count:]

    def get_latest_metric(self, metric_name: str) -> float:
        values = self._metrics.get(metric_name, [])
        return values[-1]["value"] if values else 0.0

    def get_alerts(self, severity: str = "") -> List[Dict[str, Any]]:
        alerts = self._alerts
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        return alerts

    def get_errors(self, source: str = "", count: int = 50) -> List[Dict[str, Any]]:
        errors = self._error_log
        if source:
            errors = [e for e in errors if e["source"] == source]
        return errors[-count:]

    def get_health(self) -> Dict[str, Any]:
        critical = len([a for a in self._alerts if a["severity"] == "critical"])
        errors = len([a for a in self._alerts if a["severity"] == "error"])
        return {"healthy": critical == 0, "critical_alerts": critical,
                "error_alerts": errors, "total_alerts": len(self._alerts)}

    def clear_alerts(self) -> int:
        count = len(self._alerts)
        self._alerts.clear()
        return count

    def get_stats(self) -> Dict[str, Any]:
        return {"metrics_tracked": len(self._metrics),
                "total_errors": len(self._error_log),
                "total_alerts": len(self._alerts)}
