"""RuntimeMonitor — Monitor runtime health and performance."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class RuntimeMonitor:
    """Monitor runtime with alerts, metrics tracking, and diagnostics."""

    def __init__(self) -> None:
        self._metrics_history: List[Dict[str, Any]] = []
        self._alerts: List[Dict[str, Any]] = []

    def record_snapshot(self, metrics: Dict[str, Any]) -> None:
        snapshot = {"metrics": dict(metrics), "timestamp": time.time()}
        self._metrics_history.append(snapshot)
        if len(self._metrics_history) > 1000:
            self._metrics_history = self._metrics_history[-1000:]

    def alert(self, severity: str, message: str) -> None:
        self._alerts.append({"severity": severity, "message": message,
                              "timestamp": time.time()})

    def get_alerts(self, severity: str = "") -> List[Dict[str, Any]]:
        alerts = self._alerts
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        return alerts

    def get_history(self, count: int = 10) -> List[Dict[str, Any]]:
        return self._metrics_history[-count:]

    def clear_alerts(self) -> int:
        count = len(self._alerts)
        self._alerts.clear()
        return count

    def get_stats(self) -> Dict[str, Any]:
        return {"snapshots": len(self._metrics_history), "alerts": len(self._alerts)}
