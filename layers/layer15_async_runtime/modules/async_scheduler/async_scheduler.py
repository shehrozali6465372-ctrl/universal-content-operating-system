"""Production-safe bounded async scheduler."""
from __future__ import annotations

import asyncio
import inspect
import time
import uuid
from enum import Enum
from typing import Any, Callable


class TaskState(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduledTask:
    __slots__ = ("task_id", "coro_fn", "args", "kwargs", "state", "result",
                 "error", "created_at", "started_at", "finished_at", "priority",
                 "delay_seconds", "retries", "max_retries", "metadata", "_future")

    def __init__(
        self, coro_fn: Callable[..., Any], args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None, priority: int = 0,
        delay_seconds: float = 0.0, max_retries: int = 0,
    ) -> None:
        self.task_id = str(uuid.uuid4())
        self.coro_fn = coro_fn
        self.args = args
        self.kwargs = kwargs or {}
        self.state = TaskState.PENDING
        self.result: Any = None
        self.error: str | None = None
        self.created_at = time.time()
        self.started_at = 0.0
        self.finished_at = 0.0
        self.priority = priority
        self.delay_seconds = delay_seconds
        self.retries = 0
        self.max_retries = max_retries
        self.metadata: dict[str, Any] = {}
        self._future: asyncio.Task[Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id, "state": self.state.value,
            "priority": self.priority, "retries": self.retries,
            "created_at": self.created_at, "started_at": self.started_at,
            "finished_at": self.finished_at, "error": self.error,
        }


class AsyncScheduler:
    def __init__(self, max_concurrent: int = 10) -> None:
        if max_concurrent <= 0:
            raise ValueError("max_concurrent must be positive")
        self._tasks: dict[str, ScheduledTask] = {}
        self._semaphore: asyncio.Semaphore | None = None
        self._max_concurrent = max_concurrent
        self._running_count = 0
        self._completed_count = 0
        self._failed_count = 0

    def _ensure_semaphore(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self._max_concurrent)
        return self._semaphore

    def schedule(
        self, coro_fn: Callable[..., Any], *args: Any, priority: int = 0,
        delay_seconds: float = 0.0, max_retries: int = 0,
        timeout_seconds: float = 300.0, **kwargs: Any,
    ) -> ScheduledTask:
        if not callable(coro_fn):
            raise TypeError("coro_fn must be callable")
        if delay_seconds < 0 or max_retries < 0 or timeout_seconds <= 0:
            raise ValueError("invalid delay, retry, or timeout configuration")
        task = ScheduledTask(coro_fn, args, kwargs, priority, delay_seconds, max_retries)
        task.metadata["timeout_seconds"] = timeout_seconds
        task.state = TaskState.SCHEDULED
        self._tasks[task.task_id] = task
        return task

    async def execute_task(self, task: ScheduledTask) -> dict[str, Any]:
        if task.state == TaskState.CANCELLED:
            return task.to_dict()
        sem = self._ensure_semaphore()
        async with sem:
            if task.state == TaskState.CANCELLED:
                return task.to_dict()
            task._future = asyncio.current_task()
            task.state = TaskState.RUNNING
            task.started_at = time.time()
            self._running_count += 1
            try:
                if task.delay_seconds:
                    await asyncio.sleep(task.delay_seconds)
                while True:
                    try:
                        result = task.coro_fn(*task.args, **task.kwargs)
                        if inspect.isawaitable(result):
                            result = await asyncio.wait_for(
                                result, timeout=task.metadata["timeout_seconds"]
                            )
                        task.result = result
                        task.state = TaskState.COMPLETED
                        self._completed_count += 1
                        return task.to_dict()
                    except asyncio.CancelledError:
                        task.state = TaskState.CANCELLED
                        raise
                    except Exception as exc:
                        task.error = f"{type(exc).__name__}: {exc}"
                        if task.retries >= task.max_retries:
                            task.state = TaskState.FAILED
                            self._failed_count += 1
                            return task.to_dict()
                        task.retries += 1
                        await asyncio.sleep(min(2 ** (task.retries - 1), 30))
            finally:
                task.finished_at = time.time()
                self._running_count -= 1

    async def run_all(self) -> list[dict[str, Any]]:
        pending = [t for t in self._tasks.values() if t.state == TaskState.SCHEDULED]
        pending.sort(key=lambda t: -t.priority)
        task_futures = []
        for task in pending:
            future = asyncio.create_task(self.execute_task(task))
            task._future = future
            task_futures.append(future)
        return await asyncio.gather(*task_futures)

    def cancel(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if task is None:
            return False
        if task.state in (TaskState.PENDING, TaskState.SCHEDULED):
            task.state = TaskState.CANCELLED
            return True
        if task.state == TaskState.RUNNING and task._future is not None:
            return task._future.cancel()
        return False

    def get_task(self, task_id: str) -> ScheduledTask | None:
        return self._tasks.get(task_id)

    def list_tasks(self) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self._tasks.values()]

    def stats(self) -> dict[str, Any]:
        return {
            "total": len(self._tasks), "running": self._running_count,
            "completed": self._completed_count, "failed": self._failed_count,
            "cancelled": sum(t.state == TaskState.CANCELLED for t in self._tasks.values()),
            "max_concurrent": self._max_concurrent,
        }
