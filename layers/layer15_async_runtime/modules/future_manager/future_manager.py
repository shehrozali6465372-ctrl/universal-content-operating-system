"""Async future lifecycle manager with cancellation-safe tracking."""
from __future__ import annotations

import asyncio
import inspect
import time
from enum import Enum
from typing import Any, Callable


class FutureState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ManagedFuture:
    __slots__ = ("name", "state", "result", "error", "duration_ms")

    def __init__(self, name: str) -> None:
        self.name = name
        self.state = FutureState.PENDING
        self.result: Any = None
        self.error = ""
        self.duration_ms = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "state": self.state.value, "duration_ms": round(self.duration_ms, 2)}


class FutureManager:
    def __init__(self) -> None:
        self._futures: list[ManagedFuture] = []
        self._tasks: list[asyncio.Task[Any]] = []

    def create_task(self, name: str, coro_fn: Callable[..., Any], *args: Any,
                    **kwargs: Any) -> ManagedFuture:
        mf = ManagedFuture(name)
        self._futures.append(mf)
        start = time.time()

        async def wrapper() -> None:
            mf.state = FutureState.RUNNING
            try:
                value = coro_fn(*args, **kwargs)
                mf.result = await value if inspect.isawaitable(value) else value
                mf.state = FutureState.COMPLETED
            except asyncio.CancelledError:
                mf.state = FutureState.CANCELLED
                raise
            except Exception as exc:
                mf.error = f"{type(exc).__name__}: {exc}"
                mf.state = FutureState.FAILED
            finally:
                mf.duration_ms = (time.time() - start) * 1000

        task = asyncio.create_task(wrapper())
        self._tasks.append(task)
        return mf

    def cancel_all(self) -> int:
        count = 0
        for task in self._tasks:
            if not task.done():
                task.cancel()
                count += 1
        return count

    def list_futures(self) -> list[dict[str, Any]]:
        return [future.to_dict() for future in self._futures]

    def stats(self) -> dict[str, int]:
        return {
            "total": len(self._futures),
            "completed": sum(f.state == FutureState.COMPLETED for f in self._futures),
            "failed": sum(f.state == FutureState.FAILED for f in self._futures),
            "cancelled": sum(f.state == FutureState.CANCELLED for f in self._futures),
            "running": sum(f.state == FutureState.RUNNING for f in self._futures),
        }
