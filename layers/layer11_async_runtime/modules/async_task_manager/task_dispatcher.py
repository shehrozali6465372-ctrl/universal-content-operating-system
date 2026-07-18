"""TaskDispatcher — Dispatch tasks to executors."""
from __future__ import annotations
import time
from typing import Any, Dict, List
class TaskDispatcher:
    def __init__(self): self._dispatched: List[Dict[str, Any]] = []
    def dispatch(self, task_id: str, executor_id: str = "default") -> Dict[str, Any]:
        entry = {"task_id": task_id, "executor": executor_id, "time": time.time()}
        self._dispatched.append(entry)
        return entry
    def get_history(self, count: int=20) -> List[Dict[str, Any]]: return self._dispatched[-count:]
    def get_stats(self) -> Dict[str, Any]: return {"total": len(self._dispatched)}
