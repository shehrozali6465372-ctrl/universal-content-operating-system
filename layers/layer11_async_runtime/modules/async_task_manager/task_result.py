"""TaskResult — Task result handling."""
from __future__ import annotations
import time
from typing import Any, Dict, Optional
class TaskResult:
    __slots__ = ("task_id", "success", "result", "error", "duration_ms", "completed_at")
    def __init__(self, task_id: str="", success: bool=True):
        self.task_id = task_id; self.success = success; self.result: Any = None
        self.error: Optional[str] = None; self.duration_ms: float = 0.0; self.completed_at: float = time.time()
    def to_dict(self) -> Dict[str, Any]:
        return {"task_id": self.task_id, "success": self.success, "duration_ms": round(self.duration_ms, 2)}
