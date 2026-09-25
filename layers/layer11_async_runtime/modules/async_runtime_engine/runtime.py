"""AsyncRuntime — bounded, restartable async execution engine."""
from __future__ import annotations

import asyncio
import inspect
import threading
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable, Coroutine, Dict, List, Optional

from layers.layer11_async_runtime.modules.async_task_manager.models import TaskState


class AsyncTask:
    """Runtime-local execution record."""

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

    def __init__(
        self,
        max_workers: int = 10,
        max_tracked_tasks: int = 10_000,
        task_timeout: Optional[float] = 300.0,
        shutdown_timeout: float = 30.0,
    ) -> None:
        if isinstance(max_workers, bool) or not isinstance(max_workers, int) or max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        if isinstance(max_tracked_tasks, bool) or not isinstance(max_tracked_tasks, int) or max_tracked_tasks < 1:
            raise ValueError("max_tracked_tasks must be >= 1")
        if task_timeout is not None and (
            isinstance(task_timeout, bool)
            or not isinstance(task_timeout, (int, float))
            or task_timeout <= 0
        ):
            raise ValueError("task_timeout must be > 0 or None")

        self._max_workers = max_workers
        self._max_tracked_tasks = max_tracked_tasks
        self._task_timeout = float(task_timeout) if task_timeout is not None else None
        if (isinstance(shutdown_timeout, bool) or not isinstance(shutdown_timeout, (int, float)) or shutdown_timeout <= 0):
            raise ValueError("shutdown_timeout must be > 0")
        self._shutdown_timeout = float(shutdown_timeout)
        self._thread_futures: set[Future[Any]] = set()
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        self._tasks: Dict[str, AsyncTask] = {}
        self._running = False
        self._accepting = False
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
            if self._thread_futures:
                raise RuntimeError("async runtime worker pool is still draining")
            if self._thread_pool is None:
                self._thread_pool = ThreadPoolExecutor(max_workers=self._max_workers)
            self._stopped = False
            self._running = True
            self._accepting = True

    def stop(self, timeout: Optional[float] = None) -> None:
        """Stop admission and drain blocking workers within a bounded timeout."""
        if timeout is None:
            timeout = self._shutdown_timeout
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("timeout must be > 0")
        with self._lock:
            if not self._running and self._stopped and not self._thread_futures:
                return
            self._running = False
            self._accepting = False
            pool = self._thread_pool
            self._thread_pool = None
            self._stopped = True
            futures = list(self._thread_futures)
        if pool is not None:
            pool.shutdown(wait=False, cancel_futures=True)
        deadline = time.monotonic() + float(timeout)
        while True:
            pending = [future for future in futures if not future.done()]
            if not pending:
                return
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("async runtime worker shutdown timed out")
            time.sleep(min(0.01, remaining))

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._running

    @property
    def is_accepting(self) -> bool:
        with self._lock:
            return self._running and self._accepting

    @property
    def metrics(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._metrics)

    def pause(self) -> None:
        """Stop admitting new coroutine tasks while retaining the runtime."""
        with self._lock:
            if not self._running:
                raise RuntimeError("async runtime is not running")
            self._accepting = False

    def resume(self) -> None:
        """Resume admission of new coroutine tasks."""
        with self._lock:
            if not self._running:
                raise RuntimeError("async runtime is not running")
            self._accepting = True

    def _begin_task(self, name: str) -> AsyncTask:
        with self._lock:
            if not self._running:
                raise RuntimeError("async runtime is not running")
            if not self._accepting:
                raise RuntimeError("async runtime is paused")
            task = AsyncTask(name)
            task.state = TaskState.RUNNING
            task.started_at = time.monotonic()
            self._tasks[task.task_id] = task
            self._metrics["total_tasks"] += 1
            self._prune_tasks_locked()
            return task

    def _finish_task(
        self,
        task: AsyncTask,
        state: TaskState,
        error: Optional[Exception] = None,
    ) -> None:
        with self._lock:
            task.error = error
            task.state = state
            task.finished_at = time.monotonic()
            if task.started_at is not None:
                task.duration_ms = max(
                    0.0, (task.finished_at - task.started_at) * 1000
                )
            self._metrics["total_duration_ms"] += task.duration_ms
            self._metrics[state.value] += 1
            self._prune_tasks_locked()

    def _prune_tasks_locked(self) -> None:
        if len(self._tasks) <= self._max_tracked_tasks:
            return
        finished = sorted(
            (
                task for task in self._tasks.values()
                if task.state in {
                    TaskState.COMPLETED,
                    TaskState.FAILED,
                    TaskState.CANCELLED,
                }
            ),
            key=lambda task: task.finished_at or task.created_at,
        )
        remove_count = len(self._tasks) - self._max_tracked_tasks
        for task in finished[:remove_count]:
            self._tasks.pop(task.task_id, None)

    def run_coroutine(self, coro: Coroutine[Any, Any, Any]) -> Any:
        """Run a coroutine from synchronous code."""
        if not inspect.iscoroutine(coro):
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
            raise RuntimeError(
                "run_coroutine cannot be called from a running event loop"
            )
        return asyncio.run(self.execute_coroutine(coro))

    async def execute_coroutine(self, coro: Coroutine[Any, Any, Any]) -> Any:
        """Execute one coroutine in the caller's event loop."""
        if not inspect.iscoroutine(coro):
            raise TypeError("coro must be a coroutine")
        try:
            task = self._begin_task(getattr(coro, "__name__", "coroutine"))
        except Exception:
            # Close caller-owned coroutine when admission fails.
            coro.close()
            raise
        try:
            if self._task_timeout is None:
                result = await coro
            else:
                result = await asyncio.wait_for(coro, timeout=self._task_timeout)
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
        if not coros:
            return []
        return await asyncio.gather(
            *(self.execute_coroutine(coro) for coro in coros)
        )

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

    async def _gather(
        self, coros: tuple[Coroutine[Any, Any, Any], ...]
    ) -> List[Any]:
        return await self.gather(*coros)

    def submit_to_thread(
        self,
        fn: Callable[..., Any],
        *args: Any,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> Any:
        """Run blocking work in the bounded worker pool."""
        if not callable(fn):
            raise TypeError("fn must be callable")
        if timeout is not None and (
            isinstance(timeout, bool) or timeout <= 0
        ):
            raise ValueError("timeout must be > 0 or None")
        with self._lock:
            if not self._running:
                raise RuntimeError("async runtime is not running")
            if self._thread_pool is None:
                raise RuntimeError("async runtime worker pool is unavailable")
            future = self._thread_pool.submit(fn, *args, **kwargs)
            self._thread_futures.add(future)
            future.add_done_callback(self._forget_thread_future)
        return future.result(timeout=timeout)

    async def submit_to_thread_async(
        self, fn: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """Run blocking work in the bounded worker pool from async code."""
        if not callable(fn):
            raise TypeError("fn must be callable")
        with self._lock:
            if not self._running:
                raise RuntimeError("async runtime is not running")
            pool = self._thread_pool
            if pool is None:
                raise RuntimeError("async runtime worker pool is unavailable")
        future = pool.submit(fn, *args, **kwargs)
        with self._lock:
            self._thread_futures.add(future)
            future.add_done_callback(self._forget_thread_future)
        return await asyncio.wrap_future(future)

    def _forget_thread_future(self, future: Future[Any]) -> None:
        with self._lock:
            self._thread_futures.discard(future)

    def health(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "running": self._running,
                "accepting": self._accepting,
                "task_timeout": self._task_timeout,
                "shutdown_timeout": self._shutdown_timeout,
                "max_workers": self._max_workers,
                "thread_jobs_draining": sum(1 for future in self._thread_futures if not future.done()),
                "tasks_tracked": len(self._tasks),
                "metrics": dict(self._metrics),
            }

    def get_task(self, task_id: str) -> Optional[AsyncTask]:
        with self._lock:
            return self._tasks.get(task_id)

    def list_tasks(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                {
                    "task_id": task.task_id,
                    "name": task.name,
                    "state": task.state.value,
                    "duration_ms": task.duration_ms,
                }
                for task in self._tasks.values()
            ]
