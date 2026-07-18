"""EventLoop — Wrapper around asyncio event loop."""
from __future__ import annotations
import asyncio
from typing import Any, Coroutine, Optional

class AsyncEventLoop:
    def __init__(self, loop_id: str = "main") -> None:
        self.loop_id = loop_id
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False
    def start(self) -> bool:
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._running = True
            return True
        except Exception:
            return False
    def stop(self) -> bool:
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        self._running = False
        return True
    def is_running(self) -> bool:
        return self._running
    async def run_coroutine(self, coro: Coroutine) -> Any:
        if self._loop:
            return await coro
        return None
    def run_sync(self, coro: Coroutine) -> Any:
        if self._loop and not self._loop.is_closed():
            return self._loop.run_until_complete(coro)
        return None
    def to_dict(self):
        return {"loop_id": self.loop_id, "running": self._running}
