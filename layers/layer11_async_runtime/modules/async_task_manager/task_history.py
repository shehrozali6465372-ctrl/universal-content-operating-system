"""TaskHistory — Track task execution history."""
from __future__ import annotations
import time
from typing import Any, Dict, List
class TaskHistory:
    def __init__(self, max_entries: int=1000):
        self._max = max_entries; self._entries: List[Dict[str, Any]] = []
    def record(self, task_id: str, state: str, result: Any=None):
        self._entries.append({"task_id": task_id, "state": state, "time": time.time()})
        if len(self._entries) > self._max: self._entries = self._entries[-self._max:]
    def get_recent(self, count: int=20) -> List[Dict[str, Any]]: return self._entries[-count:]
    def get_stats(self) -> Dict[str, Any]: return {"total": len(self._entries)}
