"""Production-safe async worker pool with idempotent lifecycle."""
from __future__ import annotations

import asyncio
import inspect
import time
from enum import Enum
from typing import Any, Callable


class WorkerState(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    STOPPED = "stopped"
    ERROR = "error"


class Worker:
    __slots__ = ("worker_id", "state", "current_task", "tasks_completed",
                 "tasks_failed", "started_at", "busy_since", "metadata")

    def __init__(self, worker_id: str) -> None:
        self.worker_id = worker_id
        self.state = WorkerState.IDLE
        self.current_task: str | None = None
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.started_at = time.time()
        self.busy_since = 0.0
        self.metadata: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id, "state": self.state.value,
            "tasks_completed": self.tasks_completed, "tasks_failed": self.tasks_failed,
        }


class WorkerPool:
    def __init__(self, pool_size: int = 5) -> None:
        if pool_size <= 0:
            raise ValueError("pool_size must be positive")
        self._pool_size = pool_size
        self._workers: dict[str, Worker] = {}
        self._task_queue: asyncio.Queue[tuple[str, Callable[..., Any], tuple[Any, ...], dict[str, Any]]] = asyncio.Queue()
        self._results: dict[str, dict[str, Any]] = {}
        self._running = False
        self._worker_tasks: list[asyncio.Task[Any]] = []
        self._total_processed = 0

    def initialize(self) -> None:
        if self._workers:
            return
        self._workers = {f"worker_{i}": Worker(f"worker_{i}") for i in range(self._pool_size)}

    async def submit(self, task_id: str, coro_fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        if not self._running:
            raise RuntimeError("worker pool is not running")
        if task_id in self._results:
            raise ValueError(f"task_id already completed: {task_id}")
        await self._task_queue.put((task_id, coro_fn, args, kwargs))

    async def _process_task(
        self, worker: Worker, task_id: str, coro_fn: Callable[..., Any],
        args: tuple[Any, ...], kwargs: dict[str, Any],
    ) -> None:
        worker.state = WorkerState.BUSY
        worker.current_task = task_id
        worker.busy_since = time.time()
        try:
            result = coro_fn(*args, **kwargs)
            result = await result if inspect.isawaitable(result) else result
            self._results[task_id] = {"status": "completed", "result": result}
            worker.tasks_completed += 1
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._results[task_id] = {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
            worker.tasks_failed += 1
        finally:
            worker.state = WorkerState.IDLE if self._running else WorkerState.STOPPED
            worker.current_task = None
            worker.busy_since = 0.0
            self._total_processed += 1

    async def start(self) -> None:
        if self._running:
            return
        self.initialize()
        self._running = True
        self._worker_tasks = [asyncio.create_task(self._worker_loop(w)) for w in self._workers.values()]

    async def _worker_loop(self, worker: Worker) -> None:
        while self._running:
            try:
                item = await asyncio.wait_for(self._task_queue.get(), timeout=0.2)
            except asyncio.TimeoutError:
                continue
            try:
                await self._process_task(worker, *item)
            finally:
                self._task_queue.task_done()

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        tasks = list(self._worker_tasks)
        self._worker_tasks = []
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        for worker in self._workers.values():
            worker.state = WorkerState.STOPPED

    def get_result(self, task_id: str) -> dict[str, Any] | None:
        return self._results.get(task_id)

    def list_workers(self) -> list[dict[str, Any]]:
        return [w.to_dict() for w in self._workers.values()]

    def stats(self) -> dict[str, Any]:
        idle = sum(w.state == WorkerState.IDLE for w in self._workers.values())
        busy = sum(w.state == WorkerState.BUSY for w in self._workers.values())
        return {
            "pool_size": self._pool_size, "idle": idle, "busy": busy,
            "total_processed": self._total_processed, "queue_size": self._task_queue.qsize(),
        }

    @property
    def pool_size(self) -> int:
        return self._pool_size
