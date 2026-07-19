"""ThreadPool — thread-based parallel execution pool."""
from __future__ import annotations
import concurrent.futures
import time
import uuid
from typing import Any, Callable, Dict, List, Optional


class ThreadPoolTask:
    __slots__ = ("task_id", "func", "args", "kwargs", "result",
                 "error", "submitted_at", "completed_at", "duration_ms")

    def __init__(self, func: Callable, args: tuple = (), kwargs: Optional[Dict] = None) -> None:
        self.task_id = str(uuid.uuid4())[:12]
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.result: Any = None
        self.error: Optional[str] = None
        self.submitted_at = time.time()
        self.completed_at: float = 0.0
        self.duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"task_id": self.task_id, "duration_ms": round(self.duration_ms, 2),
                "error": self.error}


class ThreadPool:
    def __init__(self, max_workers: int = 5) -> None:
        self._max_workers = max_workers
        self._executor: Optional[concurrent.futures.ThreadPoolExecutor] = None
        self._tasks: Dict[str, ThreadPoolTask] = {}
        self._futures: Dict[str, concurrent.futures.Future] = {}

    def start(self) -> None:
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers)

    def stop(self) -> None:
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None

    def submit(self, func: Callable, *args: Any, **kwargs: Any) -> ThreadPoolTask:
        if not self._executor:
            self.start()
        task = ThreadPoolTask(func, args, kwargs)
        future = self._executor.submit(func, *args, **kwargs)
        self._tasks[task.task_id] = task
        self._futures[task.task_id] = future
        return task

    def get_result(self, task_id: str, timeout: float = 5.0) -> Dict[str, Any]:
        future = self._futures.get(task_id)
        task = self._tasks.get(task_id)
        if not future or not task:
            return {"error": "not_found"}
        try:
            result = future.result(timeout=timeout)
            task.result = result
            task.completed_at = time.time()
            task.duration_ms = (task.completed_at - task.submitted_at) * 1000
            return {"status": "completed", "result": result}
        except concurrent.futures.TimeoutError:
            return {"status": "timeout"}
        except Exception as exc:
            task.error = str(exc)
            task.completed_at = time.time()
            task.duration_ms = (task.completed_at - task.submitted_at) * 1000
            return {"status": "failed", "error": str(exc)}

    def map(self, func: Callable, items: List[Any]) -> List[Any]:
        if not self._executor:
            self.start()
        results = list(self._executor.map(func, items))
        return results

    def stats(self) -> Dict[str, Any]:
        completed = sum(1 for t in self._tasks.values() if t.completed_at > 0)
        failed = sum(1 for t in self._tasks.values() if t.error)
        return {"max_workers": self._max_workers, "total_tasks": len(self._tasks),
                "completed": completed, "failed": failed}
