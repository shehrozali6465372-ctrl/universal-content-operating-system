"""Parallel Executor — Execute independent stages in parallel."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional


class ParallelTask:
    """A task to execute in parallel."""

    __slots__ = ("name", "handler", "result", "error", "duration_ms")

    def __init__(self, name: str = "", handler: Optional[Callable] = None) -> None:
        self.name = name
        self.handler = handler
        self.result: Any = None
        self.error: str = ""
        self.duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "error": self.error,
            "duration_ms": round(self.duration_ms, 2),
        }


class ParallelResult:
    """Result of parallel execution."""

    __slots__ = ("success", "tasks", "total_duration_ms")

    def __init__(self) -> None:
        self.success: bool = True
        self.tasks: List[ParallelTask] = []
        self.total_duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "task_count": len(self.tasks),
            "successful_tasks": sum(1 for t in self.tasks if not t.error),
            "failed_tasks": sum(1 for t in self.tasks if t.error),
            "total_duration_ms": round(self.total_duration_ms, 2),
        }


class ParallelExecutor:
    """Execute independent tasks in parallel (simulated)."""

    def __init__(self) -> None:
        self._parallel_count = 0

    def execute(
        self,
        tasks: List[ParallelTask],
        context: Dict[str, Any],
    ) -> ParallelResult:
        start = time.time()
        result = ParallelResult()

        for task in tasks:
            if not task.handler:
                continue
            task_start = time.time()
            try:
                task.result = task.handler(context)
            except Exception as e:
                task.error = str(e)[:500]
                result.success = False
            task.duration_ms = (time.time() - task_start) * 1000
            result.tasks.append(task)

        result.total_duration_ms = (time.time() - start) * 1000
        self._parallel_count += 1
        return result

    @property
    def parallel_count(self) -> int:
        return self._parallel_count
