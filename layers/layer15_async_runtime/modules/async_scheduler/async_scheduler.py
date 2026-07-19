"""AsyncScheduler — schedule and manage async tasks across the system."""
from __future__ import annotations
import asyncio
import time
import uuid
from typing import Any, Callable, Coroutine, Dict, List, Optional
from enum import Enum


class TaskState(str, Enum):
    PENDING = "pending"; SCHEDULED = "scheduled"; RUNNING = "running"
    COMPLETED = "completed"; FAILED = "failed"; CANCELLED = "cancelled"


class ScheduledTask:
    __slots__ = ("task_id", "coro_fn", "args", "kwargs", "state", "result",
                 "error", "created_at", "started_at", "finished_at", "priority",
                 "delay_seconds", "retries", "max_retries", "metadata")

    def __init__(self, coro_fn: Callable, args: tuple = (), kwargs: Optional[Dict] = None,
                 priority: int = 0, delay_seconds: float = 0.0,
                 max_retries: int = 0) -> None:
        self.task_id = str(uuid.uuid4())[:12]
        self.coro_fn = coro_fn
        self.args = args
        self.kwargs = kwargs or {}
        self.state = TaskState.PENDING
        self.result: Any = None
        self.error: Optional[str] = None
        self.created_at = time.time()
        self.started_at: float = 0.0
        self.finished_at: float = 0.0
        self.priority = priority
        self.delay_seconds = delay_seconds
        self.retries = 0
        self.max_retries = max_retries
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"task_id": self.task_id, "state": self.state.value,
                "priority": self.priority, "retries": self.retries,
                "created_at": self.created_at}


class AsyncScheduler:
    def __init__(self, max_concurrent: int = 10) -> None:
        self._tasks: Dict[str, ScheduledTask] = {}
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._max_concurrent = max_concurrent
        self._running_count = 0
        self._completed_count = 0
        self._failed_count = 0

    def _ensure_semaphore(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self._max_concurrent)
        return self._semaphore

    def schedule(self, coro_fn: Callable, *args: Any, priority: int = 0,
                 delay_seconds: float = 0.0, max_retries: int = 0,
                 **kwargs: Any) -> ScheduledTask:
        task = ScheduledTask(coro_fn, args, kwargs, priority, delay_seconds, max_retries)
        task.state = TaskState.SCHEDULED
        self._tasks[task.task_id] = task
        return task

    async def execute_task(self, task: ScheduledTask) -> Dict[str, Any]:
        sem = self._ensure_semaphore()
        async with sem:
            task.state = TaskState.RUNNING
            task.started_at = time.time()
            self._running_count += 1
            try:
                if task.delay_seconds > 0:
                    await asyncio.sleep(task.delay_seconds)
                coro = task.coro_fn(*task.args, **task.kwargs)
                if asyncio.iscoroutine(coro):
                    task.result = await coro
                else:
                    task.result = coro
                task.state = TaskState.COMPLETED
                self._completed_count += 1
            except Exception as exc:
                task.error = str(exc)
                if task.retries < task.max_retries:
                    task.retries += 1
                    task.state = TaskState.PENDING
                    self._running_count -= 1
                    return await self.execute_task(task)
                task.state = TaskState.FAILED
                self._failed_count += 1
            finally:
                task.finished_at = time.time()
                self._running_count -= 1
        return task.to_dict()

    async def run_all(self) -> List[Dict[str, Any]]:
        pending = [t for t in self._tasks.values() if t.state == TaskState.SCHEDULED]
        pending.sort(key=lambda t: -t.priority)
        tasks = [asyncio.create_task(self.execute_task(t)) for t in pending]
        return await asyncio.gather(*tasks, return_exceptions=False)

    def cancel(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if task and task.state in (TaskState.PENDING, TaskState.SCHEDULED):
            task.state = TaskState.CANCELLED
            return True
        return False

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        return self._tasks.get(task_id)

    def list_tasks(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self._tasks.values()]

    def stats(self) -> Dict[str, Any]:
        return {"total": len(self._tasks), "running": self._running_count,
                "completed": self._completed_count, "failed": self._failed_count,
                "max_concurrent": self._max_concurrent}
