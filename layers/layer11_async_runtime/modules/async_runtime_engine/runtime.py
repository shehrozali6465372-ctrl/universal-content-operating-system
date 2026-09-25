"""AsyncRuntime — bounded, restartable async execution engine."""
from __future__ import annotations

import asyncio
import inspect
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Coroutine, Dict, List, Optional
from layers.layer11_async_runtime.modules.async_task_manager.models import TaskState


class AsyncTask:
    __slots__ = (
        "task_id", "name", "state", "result", "error",
        "created_at", "started_at", "finished_at", "duration_ms",
    )

    def __init__(self, name: str = "unnamed") -> None:
        self.task_id = uuid.uuid4().hex
        self.name = name
        self.state = TaskState.PENDING
        self.result: Any = None
        self.error: Optional[Exception] = None
        self.created_at = time.time()
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None
        self.duration_ms = 0.0


class AsyncRuntime:
    """Thread-safe runtime for coroutine and blocking work."""

    def __init__(self, max_workers: int = 10, max_tracked_tasks: int = 10_000,\n                 task_timeout: Optional[float] = 300.0) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        if max_tracked_tasks < 1:
            raise ValueError("max_tracked_tasks must be >= 1")
        self._max_workers = max_workers
        self._max_tracked_tasks = max_tracked_tasks
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        self._tasks: Dict[str, AsyncTask] = {}
        self._running = False
        self._stopped = False
        self._lock = threading.RLock()
        self._metrics = {
            "total_tasks": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
            "total_duration_ms": 0.0,
        }

    def start(self) -> None:
        """Start or restart the runtime."""
        with self._lock:
            if self._running:
                return
            if self._thread_pool is None:
                self._thread_pool = ThreadPoolExecutor(max_workers=self._max_workers)
            self._stopped = False
            self._running = True

    def stop(self) -> None:
        """Stop the runtime and release worker resources."""
        with self._lock:
            if not self._running and self._stopped:
                return
            self._running = False
            pool = self._thread_pool
            self._thread_pool = None
            self._stopped = True
        if pool is not None:
            pool.shutdown(wait=True, cancel_futures=True)

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._running

    @property
    def metrics(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._metrics)

    def _begin_task(self, name: str) -> AsyncTask:
        with self._lock:
            if not self._running:
                raise RuntimeError("async runtime is not running")
            task = AsyncTask(name)
            task.state = TaskState.RUNNING
            task.started_at = time.monotonic()
            self._tasks[task.task_id] = task
            self._metrics["total_tasks"] += 1
            self._prune_tasks_locked()
            return task

    def _finish_task(self, task: AsyncTask, state: TaskState,
                     error: Optional[Exception] = None) -> None:
        with self._lock:
            task.error = error
            task.state = state
            task.finished_at = time.time()
            if task.started_at is not None:
                task.duration_ms = (task.finished_at - task.started_at) * 1000
            self._metrics["total_duration_ms"] += task.duration_ms
            self._metrics[state.value] += 1

    def _prune_tasks_locked(self) -> None:
        if len(self._tasks) <= self._max_tracked_tasks:
            return
        finished = sorted(
            (t for t in self._tasks.values() if t.state in {
                TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED}),
            key=lambda t: t.finished_at or t.created_at,
        )
        remove_count = len(self._tasks) - self._max_tracked_tasks
        for task in finished[:remove_count]:
            self._tasks.pop(task.task_id, None)

    def run_coroutine(self, coro: Coroutine[Any, Any, Any]) -> Any:
        """Run a coroutine from synchronous code."""
        if inspect.iscoroutine(coro) is False:
            raise TypeError("coro must be a coroutine")
        with self._lock:
            running = self._running
        if not running:
            coro.close()
            raise RuntimeError("async runtime is not running")
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            coro.close()
            raise RuntimeError("run_coroutine cannot be called from a running event loop")
        return asyncio.run(self.execute_coroutine(coro))

    async def execute_coroutine(self, coro: Coroutine[Any, Any, Any]) -> Any:
        """Execute one coroutine in the caller's event loop."""
        task = self._begin_task(getattr(coro, "__name__", "coroutine"))
        try:
            result = await coro
            task.result = result
            self._finish_task(task, TaskState.COMPLETED)
            return result
        except asyncio.CancelledError as exc:
            self._finish_task(task, TaskState.CANCELLED, exc)
            raise
        except Exception as exc:
            self._finish_task(task, TaskState.FAILED, exc)
            raise

    async def gather(self, *coros: Coroutine[Any, Any, Any]) -> List[Any]:
        """Run multiple coroutines concurrently."""
        return await asyncio.gather(*(self.execute_coroutine(c) for c in coros))

    def run_parallel(self, *coros: Coroutine[Any, Any, Any]) -> List[Any]:
        """Run multiple coroutines concurrently from synchronous code."""
        if not coros:
            return []
        with self._lock:
            running = self._running
        if not running:
            for coro in coros:
                if inspect.iscoroutine(coro):
                    coro.close()
            raise RuntimeError("async runtime is not running")
        return self.run_coroutine(self._gather(coros))

    async def _gather(self, coros: tuple[Coroutine[Any, Any, Any], ...]) -> List[Any]:
        return await self.gather(*coros)

    def submit_to_thread(self, fn: Callable[..., Any], *args: Any,
                         timeout: Optional[float] = None, **kwargs: Any) -> Any:
        """Run blocking work in the bounded worker pool."""
        if not callable(fn):
            raise TypeError("fn must be callable")
        with self._lock:
            if not self._running:
                raise RuntimeError("async runtime is not running")
            if self._thread_pool is None:
                raise RuntimeError("async runtime worker pool is unavailable")
            future = self._thread_pool.submit(fn, *args, **kwargs)
        return future.result(timeout=timeout)

    async def submit_to_thread_async(self, fn: Callable[..., Any], *args: Any,
                                     **kwargs: Any) -> Any:
        """Run blocking work in the bounded worker pool from async code."""
        if not callable(fn):
            raise TypeError("fn must be callable")
        with self._lock:
            if not self._running:
                raise RuntimeError("async runtime is not running")
            pool = self._thread_pool
            if pool is None:
                raise RuntimeError("async runtime worker pool is unavailable")
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(pool, lambda: fn(*args, **kwargs))

    def health(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "running": self._running,
                "max_workers": self._max_workers,
                "tasks_tracked": len(self._tasks),
                "metrics": dict(self._metrics),
            }

    def get_task(self, task_id: str) -> Optional[AsyncTask]:
        with self._lock:
            return self._tasks.get(task_id)

    def list_tasks(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [{
                "task_id": t.task_id,
                "name": t.name,
                "state": t.state.value,
                "duration_ms": t.duration_ms,
            } for t in self._tasks.values()]
