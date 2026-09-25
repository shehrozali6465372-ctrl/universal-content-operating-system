"""Task execution with explicit sync/async entry points."""
from __future__ import annotations

import asyncio
import inspect
import threading
import time
from typing import Any, Awaitable, Callable, Dict, Optional

from layers.layer11_async_runtime.modules.async_task_manager.task import Task


class TaskExecutor:
    """Execute tasks without nested loops and with deterministic task states."""

    def __init__(self) -> None:
        self._completed = 0
        self._failed = 0
        self._cancelled = 0
        self._lock = threading.Lock()

    @staticmethod
    def _validate(task: Task, func: Optional[Callable[..., Any]]) -> None:
        if not isinstance(task, Task):
            raise TypeError("task must be a Task")
        if func is not None and not callable(func):
            raise TypeError("func must be callable")

    @staticmethod
    def _validate_timeout(timeout: Optional[float]) -> None:
        if timeout is not None and (
            isinstance(timeout, bool) or not isinstance(timeout, (int, float))
            or timeout <= 0
        ):
            raise ValueError("timeout must be > 0 or None")

    def execute(
        self,
        task: Task,
        func: Optional[Callable[..., Any]] = None,
        *,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Execute from synchronous code; reject calls from a running loop."""
        self._validate(task, func)
        self._validate_timeout(timeout)
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            raise RuntimeError(
                "execute cannot be called from a running event loop; use execute_async"
            )
        start = time.monotonic()
        task.start()
        try:
            result = func() if func else None
            if inspect.isawaitable(result):
                result = asyncio.run(self._await_with_timeout(result, timeout))
            task.complete(result)
            self._record("completed")
            success = True
        except asyncio.CancelledError:
            task.cancel()
            self._record("cancelled")
            raise
        except Exception as exc:
            task.fail(str(exc))
            self._record("failed")
            success = False
        return {
            "task_id": task.id,
            "duration_ms": round((time.monotonic() - start) * 1000, 2),
            "success": success,
        }

    async def execute_async(
        self,
        task: Task,
        func: Optional[Callable[..., Any]] = None,
        *,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Execute from async code without creating a nested event loop."""
        self._validate(task, func)
        self._validate_timeout(timeout)
        start = time.monotonic()
        task.start()
        try:
            result = func() if func else None
            if inspect.isawaitable(result):
                result = await self._await_with_timeout(result, timeout)
            task.complete(result)
            self._record("completed")
            success = True
        except asyncio.CancelledError:
            task.cancel()
            self._record("cancelled")
            raise
        except Exception as exc:
            task.fail(str(exc))
            self._record("failed")
            success = False
        return {
            "task_id": task.id,
            "duration_ms": round((time.monotonic() - start) * 1000, 2),
            "success": success,
        }

    async def _await_with_timeout(
        self, awaitable: Awaitable[Any], timeout: Optional[float]
    ) -> Any:
        if timeout is None:
            return await awaitable
        return await asyncio.wait_for(awaitable, timeout=timeout)

    def _record(self, metric: str) -> None:
        with self._lock:
            if metric == "completed":
                self._completed += 1
            elif metric == "failed":
                self._failed += 1
            elif metric == "cancelled":
                self._cancelled += 1
            else:
                raise ValueError(f"unknown task metric: {metric}")

    def get_stats(self) -> Dict[str, int]:
        with self._lock:
            return {
                "completed": self._completed,
                "failed": self._failed,
                "cancelled": self._cancelled,
            }
