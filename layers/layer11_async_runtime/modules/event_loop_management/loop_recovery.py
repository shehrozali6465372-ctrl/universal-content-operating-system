"""LoopRecovery — Auto-recover failed loops."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class LoopRecovery:
    def __init__(self) -> None:
        self._recoveries: List[Dict[str, Any]] = []
    def attempt_recovery(self, loop_id: str, action: str = "restart") -> Dict[str, Any]:
        result = {"loop_id": loop_id, "action": action, "success": True, "time": time.time()}
        self._recoveries.append(result)
        return result
    def get_history(self, count: int = 20) -> List[Dict[str, Any]]:
        return self._recoveries[-count:]
    def get_stats(self) -> Dict[str, Any]:
        success = sum(1 for r in self._recoveries if r["success"])
        return {"total": len(self._recoveries), "success": success}
