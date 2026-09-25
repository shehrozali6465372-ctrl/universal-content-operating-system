"""Dedicated thread-owned asyncio event loop with explicit lifecycle."""
from __future__ import annotations
import asyncio
import threading
from typing import Any, Coroutine, Optional

class AsyncEventLoop:
    def __init__(self,loop_id:str="main")->None:
        self.loop_id=loop_id; self._loop:Optional[asyncio.AbstractEventLoop]=None
        self._thread:Optional[threading.Thread]=None; self._ready=threading.Event()
        self._lock=threading.RLock(); self._running=False; self._stopping=False
    def start(self)->bool:
        with self._lock:
            if self._running: return False
            self._ready.clear(); self._stopping=False
            self._thread=threading.Thread(target=self._thread_main,name=f"async-loop-{self.loop_id}",daemon=True)
            self._thread.start()
        if not self._ready.wait(5.0): self.stop(); return False
        return True
    def _thread_main(self)->None:
        loop=asyncio.new_event_loop(); asyncio.set_event_loop(loop)
        with self._lock: self._loop=loop; self._running=True; self._ready.set()
        try: loop.run_forever()
        finally:
            pending=asyncio.all_tasks(loop)
            for task in pending: task.cancel()
            if pending: loop.run_until_complete(asyncio.gather(*pending,return_exceptions=True))
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.run_until_complete(loop.shutdown_default_executor())
            loop.close()
            with self._lock: self._running=False; self._loop=None
    def stop(self,timeout:float=5.0)->bool:
        if timeout<0: raise ValueError("timeout must be >= 0")
        with self._lock:
            loop=self._loop; thread=self._thread
            if loop is None or thread is None: return False
            self._stopping=True; loop.call_soon_threadsafe(loop.stop)
        if thread is not threading.current_thread(): thread.join(timeout)
        alive=thread.is_alive()
        with self._lock:
            if not alive: self._thread=None; self._stopping=False
        return not alive
    def is_running(self)->bool:
        with self._lock: return self._running and not self._stopping
    async def run_coroutine(self,coro:Coroutine[Any,Any,Any])->Any:
        if not asyncio.iscoroutine(coro): raise TypeError("coro must be a coroutine")
        with self._lock: loop=self._loop; running=self._running and not self._stopping
        if loop is None or not running: coro.close(); raise RuntimeError("event loop is not running")
        return await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(coro,loop))
    def run_sync(self,coro:Coroutine[Any,Any,Any])->Any:
        if not asyncio.iscoroutine(coro): raise TypeError("coro must be a coroutine")
        with self._lock: loop=self._loop; thread=self._thread; running=self._running and not self._stopping
        if loop is None or thread is None or not running: coro.close(); raise RuntimeError("event loop is not running")
        if threading.current_thread() is thread: coro.close(); raise RuntimeError("run_sync cannot be called from loop thread")
        return asyncio.run_coroutine_threadsafe(coro,loop).result()
    def to_dict(self)->dict[str,Any]:
        with self._lock: return {"loop_id":self.loop_id,"running":self._running,"stopping":self._stopping}
