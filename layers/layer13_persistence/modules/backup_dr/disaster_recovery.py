"""disaster_recovery.py — Disaster recovery."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class DRPlan:
    """Disaster recovery plan."""
    __slots__ = ("plan_id", "name", "rto_seconds", "rpo_seconds",
                 "steps", "status", "last_tested")
    _counter = 0

    def __init__(self, name: str, rto_seconds: float = 3600,
                 rpo_seconds: float = 300) -> None:
        DRPlan._counter += 1
        self.plan_id: int = DRPlan._counter
        self.name = name
        self.rto_seconds = rto_seconds
        self.rpo_seconds = rpo_seconds
        self.steps: List[str] = []
        self.status: str = "active"
        self.last_tested: float = 0.0


class DisasterRecoveryManager:
    """Manages disaster recovery plans."""

    def __init__(self) -> None:
        self._plans: Dict[int, DRPlan] = {}
        self._drills: List[Dict[str, Any]] = []

    def create_plan(self, name: str, rto: float = 3600,
                    rpo: float = 300) -> DRPlan:
        plan = DRPlan(name, rto, rpo)
        self._plans[plan.plan_id] = plan
        return plan

    def get_plan(self, plan_id: int) -> DRPlan:
        return self._plans.get(plan_id)

    def run_drill(self, plan_id: int) -> bool:
        plan = self._plans.get(plan_id)
        if plan:
            plan.last_tested = time.time()
            self._drills.append({"plan_id": plan_id, "time": time.time(), "success": True})
            return True
        return False

    def get_plans(self) -> List[DRPlan]:
        return list(self._plans.values())

    def get_drills(self) -> List[Dict[str, Any]]:
        return list(self._drills)

    def stats(self) -> Dict[str, Any]:
        return {"plans": len(self._plans), "drills": len(self._drills)}
