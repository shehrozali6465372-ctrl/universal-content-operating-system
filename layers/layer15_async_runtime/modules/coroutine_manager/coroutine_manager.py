"""Production-safe coroutine lifecycle manager."""
from __future__ import annotations

import asyncio
import inspect
import time
import uuid
from enum import Enum
from typing import Any, Callable


class CoroutineState(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ManagedCoroutine:
    __slots__ = ("coro_id", "name", "coro_fn", "args", "kwargs", "state",
                 "result", "error", "task", "created_at", "started_at",
                 "finished_at", "metadata")

    def __init__(self, name: str, coro_fn: Callable[..., Any], args: tuple[Any, ...] = (),
                 kwargs: dict[str, Any] | None = None) -> None:
        self.coro_id = str(uuid.uuid4())
        self.name = name
        self.coro_fn = coro_fn
        self.args = args
        self.kwargs = kwargs or {}
        self.state = CoroutineState.CREATED
        self.result: Any = None
        self.error: str | None = None
        self.task: asyncio.Task[Any] | None = None
        self.created_at = time.time()
        self.started_at = 0.0
        self.finished_at = 0.0
        self.metadata: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "coro_id": self.coro_id, "name": self.name,
            "state": self.state.value, "created_at": self.created_at,
            "started_at": self.started_at, "finished_at": self.finished_at,
            "error": self.error,
        }


class CoroutineManager:
    def __init__(self) -> None:
        self._coroutines: dict[str, ManagedCoroutine] = {}
        self._history: list[dict[str, Any]] = {}

    def create(self, name: str, coro_fn: Callable[..., Any], *args: Any,
               **kwargs: Any) -> ManagedCoroutine:
        if not callable(coro_fn):
            raise TypeError("coro_fn must be callable")
        coro = ManagedCoroutine(name, coro_fn, args, kwargs)
        self._coroutines[coro.coro_id] = coro
        return coro

    async def _run(self, coro: ManagedCoroutine) -> dict[str, Any]:
        coro.state = CoroutineState.RUNNING
        coro.started_at = time.time()
        try:
            result = coro.coro_fn(*coro.args, **coro.kwargs)
            coro.result = await result if inspect.isawaitable(result) else result
            coro.state = CoroutineState.COMPLETED
        except asyncio.CancelledError:
            coro.state = CoroutineState.CANCELLED
            raise
        except Exception as exc:
            coro.state = CoroutineState.FAILED
            coro.error = f"{type(exc).__name__}: {exc}"
        finally:
            coro.finished_at = time.time()
            self._history.append(coro.to_dict())
        return coro.to_dict()

    async def start(self, coro_id: str) -> dict[str, Any]:
        coro = self._coroutines.get(coro_id)
        if coro is None:
            raise KeyError(f"coroutine not found: {coro_id}")
        if coro.state not in (CoroutineState.CREATED, CoroutineState.SUSPENDED):
            return coro.to_dict()
        coro.task = asyncio.current_task()
        return await self._run(coro)

    async def start_all(self) -> list[dict[str, Any]]:
        tasks = []
        for coro in self._coroutines.values():
            if coro.state == CoroutineState.CREATED:
                task = asyncio.create_task(self.start(coro.coro_id))
                coro.task = task
                tasks.append(task)
        return await asyncio.gather(*tasks)

    def cancel(self, coro_id: str) -> bool:
        coro = self._coroutines.get(coro_id)
        if coro is None:
            return False
        if coro.state == CoroutineState.CREATED:
            coro.state = CoroutineState.CANCELLED
            return True
        if coro.state == CoroutineState.RUNNING and coro.task is not None:
            return coro.task.cancel()
        return False

    def get(self, coro_id: str) -> ManagedCoroutine | None:
        return self._coroutines.get(coro_id)

    def list_coroutines(self) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self._coroutines.values()]

    def count(self) -> int:
        return len(self._coroutines)

    def get_history(self) -> list[dict[str, Any]]:
        return list(self._history)
