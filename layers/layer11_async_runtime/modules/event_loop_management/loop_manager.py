"""LoopManager — Manage multiple event loops."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer11_async_runtime.modules.event_loop_management.event_loop import AsyncEventLoop

class LoopManager:
    def __init__(self) -> None:
        self._loops: Dict[str, AsyncEventLoop] = {}
    def create_loop(self, loop_id: str) -> AsyncEventLoop:
        if loop_id not in self._loops:
            self._loops[loop_id] = AsyncEventLoop(loop_id)
        return self._loops[loop_id]
    def get_loop(self, loop_id: str) -> Optional[AsyncEventLoop]:
        return self._loops.get(loop_id)
    def remove_loop(self, loop_id: str) -> bool:
        loop = self._loops.pop(loop_id, None)
        if loop:
            loop.stop()
            return True
        return False
    def get_all(self) -> List[AsyncEventLoop]:
        return list(self._loops.values())
    def get_stats(self) -> Dict[str, Any]:
        return {"total_loops": len(self._loops),
                "running": sum(1 for l in self._loops.values() if l.is_running())}
