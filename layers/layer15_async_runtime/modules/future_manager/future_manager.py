"""FutureManager — manage async Future objects."""
from __future__ import annotations
import asyncio
import time
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class FutureState(str, Enum):
    PENDING = "pending"; RUNNING = "running"; COMPLETED = "completed"
    FAILED = "failed"; CANCELLED = "cancelled"


class ManagedFuture:
    __slots__ = ("name", "state", "result", "error", "duration_ms")

    def __init__(self, name: str) -> None:
        self.name = name
        self.state = FutureState.PENDING
        self.result: Any = None
        self.error: str = ""
        self.duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "state": self.state.value,
                "duration_ms": round(self.duration_ms, 2)}


class FutureManager:
    def __init__(self) -> None:
        self._futures: List[ManagedFuture] = []
        self._tasks: List[asyncio.Task] = []

    def create_task(self, name: str, coro_fn: Callable, *args: Any,
                    **kwargs: Any) -> ManagedFuture:
        mf = ManagedFuture(name)
        mf.state = FutureState.RUNNING
        start = time.time()

        async def wrapper():
            try:
                result = coro_fn(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
                mf.result = result
                mf.state = FutureState.COMPLETED
            except asyncio.CancelledError:
                mf.state = FutureState.CANCELLED
            except Exception as exc:
                mf.error = str(exc)
                mf.state = FutureState.FAILED
            finally:
                mf.duration_ms = (time.time() - start) * 1000

        task = asyncio.ensure_future(wrapper())
        self._tasks.append(task)
        self._futures.append(mf)
        return mf

    def cancel_all(self) -> int:
        count = 0
        for t in self._tasks:
            if not t.done():
                t.cancel()
                count += 1
        return count

    def list_futures(self) -> List[Dict[str, Any]]:
        return [m.to_dict() for m in self._futures]

    def stats(self) -> Dict[str, Any]:
        completed = sum(1 for m in self._futures if m.state == FutureState.COMPLETED)
        failed = sum(1 for m in self._futures if m.state == FutureState.FAILED)
        return {"total": len(self._futures), "completed": completed, "failed": failed,
                "cancelled": sum(1 for m in self._futures if m.state == FutureState.CANCELLED)}
