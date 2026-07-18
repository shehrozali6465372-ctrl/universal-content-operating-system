"""TaskMonitor — Monitor task execution."""
from __future__ import annotations
import time
from typing import Any, Dict, List
class TaskMonitor:
    def __init__(self): self._events: List[Dict[str, Any]] = []
    def record(self, task_id: str, event: str, data: Dict[str, Any] = None):
        self._events.append({"task_id": task_id, "event": event, "data": data or {}, "time": time.time()})
        if len(self._events) > 1000: self._events = self._events[-1000:]
    def get_events(self, task_id: str = "", count: int=20) -> List[Dict[str, Any]]:
        events = self._events
        if task_id: events = [e for e in events if e["task_id"] == task_id]
        return events[-count:]
    def get_stats(self) -> Dict[str, Any]: return {"total_events": len(self._events)}
