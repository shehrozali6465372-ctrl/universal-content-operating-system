"""Task execution with explicit sync/async entry points."""
from __future__ import annotations

import asyncio
import inspect
import threading
import time
from typing import Any, Awaitable, Callable, Dict, Optional

from layers.layer11_async_runtime.modules.async_task_manager.task import Task


class TaskExecutor:
    """Execute tasks without nesting event loops or hiding failures."""

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

    def execute(
        self,
        task: Task,
        func: Optional[Callable[..., Any]] = None,
        *,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Execute from synchronous code; reject calls from a running loop."""
        self._validate(task, func)
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            raise RuntimeError("execute cannot be called from a running event loop; use execute_async")
        start = time.monotonic()
        task.start()
        try:
            result = func() if func else None
            if inspect.isawaitable(result):
                result = asyncio.run(self._await_with_timeout(result, timeout))
            elif timeout is not None and timeout <= 0:
                raise ValueError("timeout must be > 0")
            task.complete(result)
            with self._lock:
                self._completed += 1
            success = True
        except asyncio.CancelledError:
            task.cancel()
            with self._lock:
                self._cancelled += 1
            raise
        except Exception as exc:
            task.fail(str(exc))
            with self._lock:
                self._failed += 1
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
        if timeout is not None and timeout <= 0:
            raise ValueError("timeout must be > 0")
        start = time.monotonic()
        task.start()
        try:
            result = func() if func else None
            if inspect.isawaitable(result):
                result = await self._await_with_timeout(result, timeout)
            task.complete(result)
            with self._lock:
                self._completed += 1
            success = True
        except asyncio.CancelledError:
            task.cancel()
            with self._lock:
                self._cancelled += 1
            raise
        except Exception as exc:
            task.fail(str(exc))
            with self._lock:
                self._failed += 1
            success = False
        return {
            "task_id": task.id,
            "duration_ms": round((time.monotonic() - start) * 1000, 2),
            "success": success,
        }

    @staticmethod
    async def _await_with_timeout(awaitable: Awaitable[Any], timeout: Optional[float]) -> Any:
        if timeout is None:
            return await awaitable
        return await asyncio.wait_for(awaitable, timeout=timeout)

    def get_stats(self) -> Dict[str, int]:
        with self._lock:
            return {
                "completed": self._completed,
                "failed": self._failed,
                "cancelled": self._cancelled,
            }
