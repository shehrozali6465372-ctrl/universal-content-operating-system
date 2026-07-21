"""AsyncRuntime — Real async execution engine for the entire OS."""
from __future__ import annotations
import asyncio
import time
import uuid
from typing import Any, Callable, Coroutine, Dict, List, Optional
from enum import Enum
from concurrent.futures import ThreadPoolExecutor


class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AsyncTask:
    __slots__ = ("task_id", "name", "state", "result", "error",
                 "created_at", "started_at", "finished_at", "duration_ms")

    def __init__(self, name: str = "unnamed"):
        self.task_id = str(uuid.uuid4())[:8]
        self.name = name
        self.state = TaskState.PENDING
        self.result: Any = None
        self.error: Optional[Exception] = None
        self.created_at = time.time()
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None
        self.duration_ms: float = 0.0


class AsyncRuntime:
    """Real async runtime that wraps asyncio for the Universal AI OS.

    Provides:
    - Coroutine execution
    - Parallel task execution via asyncio.gather()
    - Thread pool for blocking I/O
    - Task tracking and metrics
    """

    def __init__(self, max_workers: int = 10):
        self._max_workers = max_workers
        self._thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks: Dict[str, AsyncTask] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False
        self._metrics = {
            "total_tasks": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
            "total_duration_ms": 0.0,
        }

    def start(self) -> None:
        """Start the runtime."""
        self._running = True

    def stop(self) -> None:
        """Stop the runtime and cleanup."""
        self._running = False
        self._thread_pool.shutdown(wait=False)

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def metrics(self) -> Dict[str, Any]:
        return dict(self._metrics)

    def run_coroutine(self, coro: Coroutine) -> Any:
        """Run a coroutine synchronously (wraps asyncio.run)."""
        task = AsyncTask(name=getattr(coro, "__name__", "coroutine"))
        task.state = TaskState.RUNNING
        task.started_at = time.time()
        self._tasks[task.task_id] = task
        self._metrics["total_tasks"] += 1

        try:
            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(coro)
                task.result = result
                task.state = TaskState.COMPLETED
                self._metrics["completed"] += 1
                return result
            finally:
                loop.close()
        except Exception as e:
            task.error = e
            task.state = TaskState.FAILED
            self._metrics["failed"] += 1
            raise
        finally:
            task.finished_at = time.time()
            task.duration_ms = (task.finished_at - task.started_at) * 1000
            self._metrics["total_duration_ms"] += task.duration_ms

    async def execute_coroutine(self, coro: Coroutine) -> Any:
        """Execute a coroutine natively in an async context."""
        task = AsyncTask(name=getattr(coro, "__name__", "coroutine"))
        task.state = TaskState.RUNNING
        task.started_at = time.time()
        self._tasks[task.task_id] = task
        self._metrics["total_tasks"] += 1

        try:
            result = await coro
            task.result = result
            task.state = TaskState.COMPLETED
            self._metrics["completed"] += 1
            return result
        except Exception as e:
            task.error = e
            task.state = TaskState.FAILED
            self._metrics["failed"] += 1
            raise
        finally:
            task.finished_at = time.time()
            task.duration_ms = (task.finished_at - task.started_at) * 1000
            self._metrics["total_duration_ms"] += task.duration_ms

    async def gather(self, *coros: Coroutine) -> List[Any]:
        """Run multiple coroutines in parallel using asyncio.gather()."""
        tasks = [self.execute_coroutine(c) for c in coros]
        return await asyncio.gather(*tasks, return_exceptions=False)

    def run_parallel(self, *coros: Coroutine) -> List[Any]:
        """Run multiple coroutines in parallel (sync wrapper)."""
        async def _gather():
            return await self.gather(*coros)
        return self.run_coroutine(_gather())

    def submit_to_thread(self, fn: Callable, *args, **kwargs) -> Any:
        """Run a blocking function in the thread pool."""
        future = self._thread_pool.submit(fn, *args, **kwargs)
        return future.result(timeout=30)

    async def submit_to_thread_async(self, fn: Callable, *args, **kwargs) -> Any:
        """Run a blocking function in the thread pool (async version)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._thread_pool, lambda: fn(*args, **kwargs))

    def health(self) -> Dict[str, Any]:
        """Return runtime health status."""
        return {
            "running": self._running,
            "max_workers": self._max_workers,
            "tasks_tracked": len(self._tasks),
            "metrics": self.metrics,
        }

    def get_task(self, task_id: str) -> Optional[AsyncTask]:
        return self._tasks.get(task_id)

    def list_tasks(self) -> List[Dict[str, Any]]:
        return [{
            "task_id": t.task_id,
            "name": t.name,
            "state": t.state.value,
            "duration_ms": t.duration_ms,
        } for t in self._tasks.values()]
