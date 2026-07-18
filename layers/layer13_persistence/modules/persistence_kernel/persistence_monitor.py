"""persistence_monitor.py — Real-time persistence monitoring."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class PersistenceMonitor:
    """Monitors persistence system in real-time."""

    def __init__(self) -> None:
        self._metrics: Dict[str, List[Dict[str, Any]]] = {}
        self._alerts: List[Dict[str, Any]] = []
        self._thresholds: Dict[str, float] = {}

    def set_threshold(self, metric: str, value: float) -> None:
        self._thresholds[metric] = value

    def record(self, metric: str, value: float) -> None:
        if metric not in self._metrics:
            self._metrics[metric] = []
        self._metrics[metric].append({"value": value, "time": time.time()})
        if len(self._metrics[metric]) > 1000:
            self._metrics[metric] = self._metrics[metric][-1000:]
        threshold = self._thresholds.get(metric)
        if threshold and value > threshold:
            self._alerts.append({"metric": metric, "value": value,
                                  "threshold": threshold, "time": time.time()})

    def get_metric(self, metric: str, limit: int = 100) -> List[Dict[str, Any]]:
        return self._metrics.get(metric, [])[-limit:]

    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._alerts[-limit:]

    def clear_alerts(self) -> int:
        count = len(self._alerts)
        self._alerts.clear()
        return count

    def stats(self) -> Dict[str, Any]:
        return {"metrics": len(self._metrics), "alerts": len(self._alerts),
                "thresholds": len(self._thresholds)}
