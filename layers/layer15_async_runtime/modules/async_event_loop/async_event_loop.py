"""AsyncEventLoop — manage and monitor async event loops."""
from __future__ import annotations
import asyncio
import time
import uuid
from typing import Any, Callable, Coroutine, Dict, List, Optional
from enum import Enum


class LoopState(str, Enum):
    CREATED = "created"; RUNNING = "running"; STOPPED = "stopped"; ERROR = "error"


class EventLoopInfo:
    __slots__ = ("loop_id", "state", "created_at", "started_at", "stopped_at",
                 "tasks_spawned", "tasks_completed", "metadata")

    def __init__(self, loop_id: str) -> None:
        self.loop_id = loop_id
        self.state = LoopState.CREATED
        self.created_at = time.time()
        self.started_at: float = 0.0
        self.stopped_at: float = 0.0
        self.tasks_spawned = 0
        self.tasks_completed = 0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"loop_id": self.loop_id, "state": self.state.value,
                "tasks_spawned": self.tasks_spawned,
                "tasks_completed": self.tasks_completed}


class AsyncEventLoop:
    def __init__(self) -> None:
        self._loops: Dict[str, EventLoopInfo] = {}
        self._active_loop: Optional[asyncio.AbstractEventLoop] = None

    def create_loop(self, loop_id: Optional[str] = None) -> EventLoopInfo:
        lid = loop_id or str(uuid.uuid4())[:12]
        info = EventLoopInfo(lid)
        self._loops[lid] = info
        return info

    def set_active_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._active_loop = loop

    def get_active_loop(self) -> Optional[asyncio.AbstractEventLoop]:
        return self._active_loop

    async def run_coroutine(self, coro: Coroutine) -> Any:
        info = list(self._loops.values())
        if info:
            info[-1].tasks_spawned += 1
        result = await coro
        if info:
            info[-1].tasks_completed += 1
        return result

    def run_until_complete(self, coro: Coroutine) -> Any:
        if not self._active_loop:
            self._active_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._active_loop)
        return self._active_loop.run_until_complete(coro)

    def stop_loop(self, loop_id: str) -> bool:
        info = self._loops.get(loop_id)
        if info:
            info.state = LoopState.STOPPED
            info.stopped_at = time.time()
            return True
        return False

    def list_loops(self) -> List[Dict[str, Any]]:
        return [l.to_dict() for l in self._loops.values()]

    def stats(self) -> Dict[str, Any]:
        total_spawned = sum(l.tasks_spawned for l in self._loops.values())
        total_completed = sum(l.tasks_completed for l in self._loops.values())
        return {"total_loops": len(self._loops), "active_loop": self._active_loop is not None,
                "tasks_spawned": total_spawned, "tasks_completed": total_completed}

    def count(self) -> int:
        return len(self._loops)
