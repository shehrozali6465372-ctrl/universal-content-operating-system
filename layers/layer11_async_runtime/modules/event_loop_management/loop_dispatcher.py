"""LoopDispatcher — Dispatch tasks to loops."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class LoopDispatcher:
    def __init__(self) -> None:
        self._dispatched: List[Dict[str, Any]] = []
    def dispatch(self, loop_id: str, task_name: str) -> Dict[str, Any]:
        entry = {"loop_id": loop_id, "task": task_name, "time": time.time()}
        self._dispatched.append(entry)
        return entry
    def get_history(self, count: int = 20) -> List[Dict[str, Any]]:
        return self._dispatched[-count:]
    def get_stats(self) -> Dict[str, Any]:
        return {"total_dispatched": len(self._dispatched)}
