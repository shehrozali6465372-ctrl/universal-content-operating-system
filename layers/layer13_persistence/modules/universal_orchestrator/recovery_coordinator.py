"""recovery_coordinator.py — Recovery coordination."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class RecoveryCoordinator:
    """Coordinates recovery across all stores."""

    def __init__(self) -> None:
        self._recovery_plans: Dict[str, List[str]] = {}
        self._last_recovery: float = 0.0
        self._recovery_count: int = 0

    def register_plan(self, store_name: str, steps: List[str]) -> None:
        self._recovery_plans[store_name] = steps

    def execute_recovery(self, store_name: str) -> bool:
        if store_name in self._recovery_plans:
            self._last_recovery = time.time()
            self._recovery_count += 1
            return True
        return False

    def get_plan(self, store_name: str) -> List[str]:
        return list(self._recovery_plans.get(store_name, []))

    def stats(self) -> Dict[str, Any]:
        return {"plans": len(self._recovery_plans), "recoveries": self._recovery_count}
