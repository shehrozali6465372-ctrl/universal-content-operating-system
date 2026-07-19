"""AIMonitor — real-time monitoring for orchestrator."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class AIMonitor:
    def __init__(self) -> None:
        self._alerts: List[Dict[str, Any]] = []; self._start = time.time()
        self._counters: Dict[str, int] = {}
    def increment(self, metric: str, amount: int = 1) -> None:
        self._counters[metric] = self._counters.get(metric, 0) + amount
    def alert(self, level: str, message: str) -> None:
        self._alerts.append({"level": level, "message": message, "time": time.time()})
    def get_alerts(self, level: str | None = None) -> List[Dict[str, Any]]:
        if level: return [a for a in self._alerts if a["level"] == level]
        return list(self._alerts)
    def status(self) -> Dict[str, Any]:
        return {"uptime": round(time.time() - self._start, 2), "counters": dict(self._counters)}
    def reset(self) -> None: self._alerts.clear(); self._counters.clear(); self._start = time.time()
