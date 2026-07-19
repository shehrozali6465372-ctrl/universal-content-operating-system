"""ReasoningMonitor — monitor reasoning system health in real-time."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional


class ReasoningMonitor:
    """Monitor the reasoning engine system in real-time."""

    def __init__(self) -> None:
        self._alerts: List[Dict[str, Any]] = []
        self._start_time = time.time()
        self._counters: Dict[str, int] = {}

    def increment(self, metric: str, amount: int = 1) -> None:
        self._counters[metric] = self._counters.get(metric, 0) + amount

    def alert(self, level: str, message: str) -> None:
        self._alerts.append({"level": level, "message": message, "time": time.time()})

    def get_alerts(self, level: Optional[str] = None) -> List[Dict[str, Any]]:
        if level:
            return [a for a in self._alerts if a["level"] == level]
        return list(self._alerts)

    def get_counter(self, metric: str) -> int:
        return self._counters.get(metric, 0)

    def status(self) -> Dict[str, Any]:
        return {"uptime": round(time.time() - self._start_time, 2),
                "counters": dict(self._counters),
                "alert_count": len(self._alerts)}

    def reset(self) -> None:
        self._alerts.clear()
        self._counters.clear()
        self._start_time = time.time()
