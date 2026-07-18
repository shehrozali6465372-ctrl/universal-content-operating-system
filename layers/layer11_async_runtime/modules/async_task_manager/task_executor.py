"""TaskExecutor — Execute tasks."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict
from layers.layer11_async_runtime.modules.async_task_manager.task import Task

class TaskExecutor:
    def __init__(self): self._completed = 0; self._failed = 0
    def execute(self, task: Task, func: Callable = None) -> Dict[str, Any]:
        start = time.time()
        task.start()
        try:
            result = func() if func else None
            task.complete(result)
            self._completed += 1
        except Exception as e:
            task.fail(str(e))
            self._failed += 1
        return {"task_id": task.id, "duration_ms": round((time.time()-start)*1000, 2), "success": task.state == "completed"}
    def get_stats(self) -> Dict[str, Any]: return {"completed": self._completed, "failed": self._failed}
