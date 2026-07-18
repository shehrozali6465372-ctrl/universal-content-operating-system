"""TaskMemory — Store task state for recovery."""
from __future__ import annotations
import time
from typing import Any, Dict, List
class TaskMemory:
    def __init__(self, max_entries: int=500):
        self._max = max_entries; self._entries: List[Dict[str, Any]] = []
    def store(self, task_id: str, state: Dict[str, Any]):
        self._entries.append({"task_id": task_id, "state": state, "time": time.time()})
        if len(self._entries) > self._max: self._entries = self._entries[-self._max:]
    def get(self, task_id: str) -> Dict[str, Any]:
        for e in reversed(self._entries):
            if e["task_id"] == task_id: return e
        return {}
    def get_stats(self) -> Dict[str, Any]: return {"total": len(self._entries)}
