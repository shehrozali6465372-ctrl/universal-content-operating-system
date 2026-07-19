"""CoroutineManager — manage lifecycle of async coroutines."""
from __future__ import annotations
import asyncio
import time
import uuid
from typing import Any, Callable, Coroutine, Dict, List, Optional
from enum import Enum


class CoroutineState(str, Enum):
    CREATED = "created"; RUNNING = "running"; SUSPENDED = "suspended"
    COMPLETED = "completed"; FAILED = "failed"; CANCELLED = "cancelled"


class ManagedCoroutine:
    __slots__ = ("coro_id", "name", "coro_fn", "args", "kwargs", "state",
                 "result", "error", "task", "created_at", "started_at",
                 "finished_at", "metadata")

    def __init__(self, name: str, coro_fn: Callable, args: tuple = (),
                 kwargs: Optional[Dict] = None) -> None:
        self.coro_id = str(uuid.uuid4())[:12]
        self.name = name
        self.coro_fn = coro_fn
        self.args = args
        self.kwargs = kwargs or {}
        self.state = CoroutineState.CREATED
        self.result: Any = None
        self.error: Optional[str] = None
        self.task: Optional[asyncio.Task] = None
        self.created_at = time.time()
        self.started_at: float = 0.0
        self.finished_at: float = 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"coro_id": self.coro_id, "name": self.name,
                "state": self.state.value, "created_at": self.created_at}


class CoroutineManager:
    def __init__(self) -> None:
        self._coroutines: Dict[str, ManagedCoroutine] = {}
        self._history: List[Dict[str, Any]] = []

    def create(self, name: str, coro_fn: Callable, *args: Any,
               **kwargs: Any) -> ManagedCoroutine:
        coro = ManagedCoroutine(name, coro_fn, args, kwargs)
        self._coroutines[coro.coro_id] = coro
        return coro

    async def start(self, coro_id: str) -> Dict[str, Any]:
        coro = self._coroutines.get(coro_id)
        if not coro:
            return {"error": "not_found"}
        coro.state = CoroutineState.RUNNING
        coro.started_at = time.time()
        try:
            result = coro.coro_fn(*coro.args, **coro.kwargs)
            if asyncio.iscoroutine(result):
                coro.result = await result
            else:
                coro.result = result
            coro.state = CoroutineState.COMPLETED
        except asyncio.CancelledError:
            coro.state = CoroutineState.CANCELLED
        except Exception as exc:
            coro.state = CoroutineState.FAILED
            coro.error = str(exc)
        coro.finished_at = time.time()
        entry = coro.to_dict()
        self._history.append(entry)
        return entry

    async def start_all(self) -> List[Dict[str, Any]]:
        tasks = []
        for coro_id in self._coroutines:
            if self._coroutines[coro_id].state == CoroutineState.CREATED:
                tasks.append(self.start(coro_id))
        return await asyncio.gather(*tasks, return_exceptions=False)

    def cancel(self, coro_id: str) -> bool:
        coro = self._coroutines.get(coro_id)
        if coro and coro.task and not coro.task.done():
            coro.task.cancel()
            coro.state = CoroutineState.CANCELLED
            return True
        if coro and coro.state == CoroutineState.CREATED:
            coro.state = CoroutineState.CANCELLED
            return True
        return False

    def get(self, coro_id: str) -> Optional[ManagedCoroutine]:
        return self._coroutines.get(coro_id)

    def list_coroutines(self) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self._coroutines.values()]

    def count(self) -> int:
        return len(self._coroutines)

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
