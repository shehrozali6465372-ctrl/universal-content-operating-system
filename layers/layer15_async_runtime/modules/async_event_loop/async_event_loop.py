"""Production-safe async event-loop lifecycle manager."""
from __future__ import annotations

import asyncio
import time
import uuid
from enum import Enum
from typing import Any, Coroutine


class LoopState(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class EventLoopInfo:
    __slots__ = ("loop_id", "state", "created_at", "started_at", "stopped_at",
                 "tasks_spawned", "tasks_completed", "metadata")

    def __init__(self, loop_id: str) -> None:
        self.loop_id = loop_id
        self.state = LoopState.CREATED
        self.created_at = time.time()
        self.started_at = 0.0
        self.stopped_at = 0.0
        self.tasks_spawned = 0
        self.tasks_completed = 0
        self.metadata: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "loop_id": self.loop_id,
            "state": self.state.value,
            "tasks_spawned": self.tasks_spawned,
            "tasks_completed": self.tasks_completed,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
        }


class AsyncEventLoop:
    def __init__(self) -> None:
        self._loops: dict[str, EventLoopInfo] = {}
        self._active_loop: asyncio.AbstractEventLoop | None = None

    def create_loop(self, loop_id: str | None = None) -> EventLoopInfo:
        lid = loop_id or str(uuid.uuid4())
        if lid in self._loops:
            raise ValueError(f"loop_id already exists: {lid}")
        info = EventLoopInfo(lid)
        self._loops[lid] = info
        return info

    def set_active_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        if loop.is_closed():
            raise ValueError("cannot activate a closed event loop")
        self._active_loop = loop

    def get_active_loop(self) -> asyncio.AbstractEventLoop | None:
        return self._active_loop

    async def run_coroutine(self, coro: Coroutine[Any, Any, Any]) -> Any:
        if not asyncio.iscoroutine(coro):
            raise TypeError("coro must be a coroutine")
        info = next(
            (item for item in reversed(list(self._loops.values()))
             if item.state in (LoopState.CREATED, LoopState.RUNNING)),
            None,
        )
        if info:
            info.tasks_spawned += 1
            info.state = LoopState.RUNNING
        try:
            result = await coro
        except BaseException:
            if info:
                info.state = LoopState.ERROR
            raise
        else:
            if info:
                info.tasks_completed += 1
            return result

    def run_until_complete(self, coro: Coroutine[Any, Any, Any]) -> Any:
        if not asyncio.iscoroutine(coro):
            raise TypeError("coro must be a coroutine")
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            coro.close()
            raise RuntimeError("cannot run_until_complete from a running event loop")
        if self._active_loop is not None and self._active_loop.is_running():
            coro.close()
            raise RuntimeError("cannot run_until_complete while the active loop is running")
        if self._active_loop is None or self._active_loop.is_closed():
            self._active_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._active_loop)
        try:
            return self._active_loop.run_until_complete(self.run_coroutine(coro))
        finally:
            asyncio.set_event_loop(None)

    def stop_loop(self, loop_id: str) -> bool:
        info = self._loops.get(loop_id)
        if info is None:
            return False
        info.state = LoopState.STOPPED
        info.stopped_at = time.time()
        return True

    def list_loops(self) -> list[dict[str, Any]]:
        return [loop.to_dict() for loop in self._loops.values()]

    def stats(self) -> dict[str, Any]:
        return {
            "total_loops": len(self._loops),
            "active_loop": self._active_loop is not None
            and not self._active_loop.is_closed(),
            "tasks_spawned": sum(l.tasks_spawned for l in self._loops.values()),
            "tasks_completed": sum(l.tasks_completed for l in self._loops.values()),
        }

    def count(self) -> int:
        return len(self._loops)
