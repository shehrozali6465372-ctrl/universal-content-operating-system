"""CostMonitor — real-time cost monitoring."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

class CostMonitor:
    def __init__(self) -> None:
        self._alerts: List[Dict[str, Any]] = []
        self._start = time.time()
        self._counters: Dict[str, float] = {}
    def add_spend(self, amount: float) -> None:
        self._counters["total_spend"] = self._counters.get("total_spend", 0) + amount
    def alert(self, level: str, message: str) -> None:
        self._alerts.append({"level": level, "message": message, "time": time.time()})
    def get_alerts(self, level: Optional[str] = None) -> List[Dict[str, Any]]:
        if level: return [a for a in self._alerts if a["level"] == level]
        return list(self._alerts)
    def status(self) -> Dict[str, Any]:
        return {"uptime": round(time.time() - self._start, 2), "counters": dict(self._counters)}
    def reset(self) -> None:
        self._alerts.clear(); self._counters.clear(); self._start = time.time()
