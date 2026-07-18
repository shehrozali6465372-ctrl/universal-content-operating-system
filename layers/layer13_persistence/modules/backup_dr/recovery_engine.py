"""recovery_engine.py — Recovery engine."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class RecoveryPlan:
    """A recovery plan."""
    __slots__ = ("plan_id", "steps", "status", "created_at", "completed_at")
    _counter = 0

    def __init__(self, steps: List[str] = None) -> None:
        RecoveryPlan._counter += 1
        self.plan_id: int = RecoveryPlan._counter
        self.steps = steps or []
        self.status: str = "pending"
        self.created_at: float = time.time()
        self.completed_at: float = 0.0


class RecoveryEngine:
    """Executes recovery plans."""

    def __init__(self) -> None:
        self._plans: Dict[int, RecoveryPlan] = {}
        self._executed: List[RecoveryPlan] = []

    def create_plan(self, steps: List[str] = None) -> RecoveryPlan:
        plan = RecoveryPlan(steps)
        self._plans[plan.plan_id] = plan
        return plan

    def execute(self, plan_id: int) -> bool:
        plan = self._plans.get(plan_id)
        if plan:
            plan.status = "executed"
            plan.completed_at = time.time()
            self._executed.append(plan)
            return True
        return False

    def get_plan(self, plan_id: int) -> RecoveryPlan:
        return self._plans.get(plan_id)

    def get_executed(self) -> List[RecoveryPlan]:
        return list(self._executed)

    def stats(self) -> Dict[str, Any]:
        return {"plans": len(self._plans), "executed": len(self._executed)}
