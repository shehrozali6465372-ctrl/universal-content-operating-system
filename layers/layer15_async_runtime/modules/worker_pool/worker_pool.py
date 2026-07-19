"""WorkerPool — manage a pool of async workers for task execution."""
from __future__ import annotations
import asyncio
import time
import uuid
from typing import Any, Callable, Coroutine, Dict, List, Optional
from enum import Enum


class WorkerState(str, Enum):
    IDLE = "idle"; BUSY = "busy"; STOPPED = "stopped"; ERROR = "error"


class Worker:
    __slots__ = ("worker_id", "state", "current_task", "tasks_completed",
                 "tasks_failed", "started_at", "busy_since", "metadata")

    def __init__(self, worker_id: str) -> None:
        self.worker_id = worker_id
        self.state = WorkerState.IDLE
        self.current_task: Optional[str] = None
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.started_at = time.time()
        self.busy_since: float = 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"worker_id": self.worker_id, "state": self.state.value,
                "tasks_completed": self.tasks_completed,
                "tasks_failed": self.tasks_failed}


class WorkerPool:
    def __init__(self, pool_size: int = 5) -> None:
        self._pool_size = pool_size
        self._workers: Dict[str, Worker] = {}
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._results: Dict[str, Any] = {}
        self._running = False
        self._total_processed = 0

    def initialize(self) -> None:
        for i in range(self._pool_size):
            wid = f"worker_{i}"
            self._workers[wid] = Worker(wid)

    async def submit(self, task_id: str, coro_fn: Callable, *args: Any,
                     **kwargs: Any) -> None:
        await self._task_queue.put((task_id, coro_fn, args, kwargs))

    async def _process_task(self, worker: Worker, task_id: str,
                            coro_fn: Callable, args: tuple, kwargs: Dict) -> None:
        worker.state = WorkerState.BUSY
        worker.current_task = task_id
        worker.busy_since = time.time()
        try:
            result = coro_fn(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            self._results[task_id] = {"status": "completed", "result": result}
            worker.tasks_completed += 1
        except Exception as exc:
            self._results[task_id] = {"status": "failed", "error": str(exc)}
            worker.tasks_failed += 1
        finally:
            worker.state = WorkerState.IDLE
            worker.current_task = None
            self._total_processed += 1

    async def start(self) -> None:
        self._running = True
        self.initialize()
        workers = list(self._workers.values())
        async def worker_loop(w: Worker):
            while self._running:
                try:
                    task_id, coro_fn, args, kwargs = await asyncio.wait_for(
                        self._task_queue.get(), timeout=1.0)
                    await self._process_task(w, task_id, coro_fn, args, kwargs)
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    w.state = WorkerState.ERROR
        self._worker_tasks = [asyncio.create_task(worker_loop(w)) for w in workers]

    async def stop(self) -> None:
        self._running = False
        for task in getattr(self, '_worker_tasks', []):
            task.cancel()
        for w in self._workers.values():
            w.state = WorkerState.STOPPED

    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self._results.get(task_id)

    def list_workers(self) -> List[Dict[str, Any]]:
        return [w.to_dict() for w in self._workers.values()]

    def stats(self) -> Dict[str, Any]:
        idle = sum(1 for w in self._workers.values() if w.state == WorkerState.IDLE)
        busy = sum(1 for w in self._workers.values() if w.state == WorkerState.BUSY)
        return {"pool_size": self._pool_size, "idle": idle, "busy": busy,
                "total_processed": self._total_processed,
                "queue_size": self._task_queue.qsize()}

    @property
    def pool_size(self) -> int:
        return self._pool_size
