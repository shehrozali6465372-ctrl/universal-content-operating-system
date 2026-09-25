"""Dedicated thread-owned asyncio event loop with explicit lifecycle."""
from __future__ import annotations

import asyncio
import threading
from concurrent.futures import Future
from typing import Any, Coroutine, Optional


class AsyncEventLoop:
    """Own exactly one asyncio loop from one dedicated thread."""

    def __init__(self, loop_id: str = "main", startup_timeout: float = 5.0) -> None:
        if not isinstance(loop_id, str) or not loop_id:
            raise ValueError("loop_id must be non-empty")
        if startup_timeout <= 0:
            raise ValueError("startup_timeout must be > 0")
        self.loop_id = loop_id
        self._startup_timeout = startup_timeout
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._ready = threading.Event()
        self._lock = threading.RLock()
        self._running = False
        self._stopping = False

    def start(self) -> bool:
        with self._lock:
            if self._running:
                return False
            if self._thread is not None and self._thread.is_alive():
                return False
            self._ready.clear()
            self._stopping = False
            self._thread = threading.Thread(
                target=self._thread_main,
                name=f"async-loop-{self.loop_id}",
                daemon=True,
            )
            self._thread.start()
        if not self._ready.wait(self._startup_timeout):
            self.stop(timeout=0)
            return False
        return self.is_running()

    def _thread_main(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        with self._lock:
            self._loop = loop
            self._running = True
            self._ready.set()
        try:
            loop.run_forever()
        finally:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(
                    asyncio.gather(*pending, return_exceptions=True)
                )
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.run_until_complete(loop.shutdown_default_executor())
            loop.close()
            with self._lock:
                self._running = False
                self._loop = None
                self._stopping = False

    def stop(self, timeout: float = 5.0) -> bool:
        if isinstance(timeout, bool) or timeout < 0:
            raise ValueError("timeout must be >= 0")
        with self._lock:
            loop = self._loop
            thread = self._thread
            if loop is None or thread is None:
                return False
            self._stopping = True
            loop.call_soon_threadsafe(loop.stop)
        if thread is not threading.current_thread():
            thread.join(timeout)
        alive = thread.is_alive()
        with self._lock:
            if not alive:
                self._thread = None
                self._stopping = False
        return not alive

    def is_running(self) -> bool:
        with self._lock:
            return self._running and not self._stopping

    async def run_coroutine(self, coro: Coroutine[Any, Any, Any]) -> Any:
        """Submit a coroutine to the owned loop from another async context."""
        if not asyncio.iscoroutine(coro):
            raise TypeError("coro must be a coroutine")
        with self._lock:
            loop = self._loop
            running = self._running and not self._stopping
        if loop is None or not running:
            coro.close()
            raise RuntimeError("event loop is not running")
        future: Future[Any] = asyncio.run_coroutine_threadsafe(coro, loop)
        try:
            return await asyncio.wrap_future(future)
        except asyncio.CancelledError:
            future.cancel()
            raise

    def run_sync(
        self,
        coro: Coroutine[Any, Any, Any],
        timeout: Optional[float] = None,
    ) -> Any:
        """Submit a coroutine from synchronous code with optional timeout."""
        if not asyncio.iscoroutine(coro):
            raise TypeError("coro must be a coroutine")
        if timeout is not None and (isinstance(timeout, bool) or timeout <= 0):
            coro.close()
            raise ValueError("timeout must be > 0 or None")
        with self._lock:
            loop = self._loop
            thread = self._thread
            running = self._running and not self._stopping
        if loop is None or thread is None or not running:
            coro.close()
            raise RuntimeError("event loop is not running")
        if threading.current_thread() is thread:
            coro.close()
            raise RuntimeError("run_sync cannot be called from loop thread")
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        try:
            return future.result(timeout=timeout)
        except TimeoutError:
            future.cancel()
            raise

    def to_dict(self) -> dict[str, Any]:
        with self._lock:
            return {
                "loop_id": self.loop_id,
                "running": self._running,
                "stopping": self._stopping,
            }
