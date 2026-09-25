"""SystemMonitor — bounded health, metric, and error history."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class SystemMonitor:
    def __init__(self, max_history: int = 10000) -> None:
        if max_history <= 0:
            raise ValueError("max_history must be positive")
        self._max_history = max_history
        self._metrics: Dict[str, List[Dict[str, Any]]] = {}
        self._alerts: List[Dict[str, Any]] = []
        self._error_log: List[Dict[str, Any]] = []

    def record_metric(self, metric_name: str, value: float,
                      tags: Optional[Dict[str, str]] = None) -> None:
        history = self._metrics.setdefault(metric_name, [])
        history.append({"value": value, "timestamp": time.time(), "tags": dict(tags or {})})
        if len(history) > self._max_history:
            del history[:-self._max_history]

    def record_error(self, source: str, error: str, severity: str = "warning") -> None:
        record = {"source": source, "error": error, "severity": severity, "timestamp": time.time()}
        self._error_log.append(record)
        if len(self._error_log) > self._max_history:
            del self._error_log[:-self._max_history]
        if severity in ("error", "critical"):
            self._alerts.append(record.copy())
            if len(self._alerts) > self._max_history:
                del self._alerts[:-self._max_history]

    def get_metric(self, metric_name: str, count: int = 10) -> List[Dict[str, Any]]:
        return list(self._metrics.get(metric_name, [])[-max(0, count):])

    def get_latest_metric(self, metric_name: str) -> float:
        values = self._metrics.get(metric_name, [])
        return values[-1]["value"] if values else 0.0

    def get_alerts(self, severity: str = "") -> List[Dict[str, Any]]:
        return list(self._alerts if not severity else [
            alert for alert in self._alerts if alert["severity"] == severity
        ])

    def get_errors(self, source: str = "", count: int = 50) -> List[Dict[str, Any]]:
        errors = self._error_log if not source else [
            error for error in self._error_log if error["source"] == source
        ]
        return list(errors[-max(0, count):])

    def get_health(self) -> Dict[str, Any]:
        critical = sum(alert["severity"] == "critical" for alert in self._alerts)
        errors = sum(alert["severity"] == "error" for alert in self._alerts)
        return {"healthy": critical == 0, "critical_alerts": critical,
                "error_alerts": errors, "total_alerts": len(self._alerts)}

    def clear_alerts(self) -> int:
        count = len(self._alerts)
        self._alerts.clear()
        return count

    def get_stats(self) -> Dict[str, Any]:
        return {"metrics_tracked": len(self._metrics), "total_errors": len(self._error_log),
                "total_alerts": len(self._alerts)}
