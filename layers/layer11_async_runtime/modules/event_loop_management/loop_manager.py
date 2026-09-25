"""Thread-safe manager for multiple owned event loops."""
from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from layers.layer11_async_runtime.modules.event_loop_management.event_loop import AsyncEventLoop


class LoopManager:
    def __init__(self) -> None:
        self._loops: Dict[str, AsyncEventLoop] = {}
        self._lock = threading.RLock()

    def create_loop(self, loop_id: str) -> AsyncEventLoop:
        if not isinstance(loop_id, str) or not loop_id:
            raise ValueError("loop_id must be non-empty")
        with self._lock:
            loop = self._loops.get(loop_id)
            if loop is None:
                loop = AsyncEventLoop(loop_id)
                self._loops[loop_id] = loop
            return loop

    def get_loop(self, loop_id: str) -> Optional[AsyncEventLoop]:
        with self._lock:
            return self._loops.get(loop_id)

    def remove_loop(self, loop_id: str) -> bool:
        with self._lock:
            loop = self._loops.pop(loop_id, None)
        if loop is None:
            return False
        return loop.stop()

    def get_all(self) -> List[AsyncEventLoop]:
        with self._lock:
            return list(self._loops.values())

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            loops = list(self._loops.values())
        return {
            "total_loops": len(loops),
            "running": sum(1 for loop in loops if loop.is_running()),
        }
