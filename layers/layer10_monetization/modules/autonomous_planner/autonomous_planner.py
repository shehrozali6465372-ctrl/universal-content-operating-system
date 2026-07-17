"""AutonomousPlanner — Long-term planning with dynamic replanning."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_AP_COUNTER = itertools.count(1)


class PlanStep:
    """A single step in an autonomous plan."""

    __slots__ = ("step_id", "layer", "action", "status", "result", "order")

    def __init__(self, layer: str = "", action: str = "", order: int = 0) -> None:
        self.step_id: str = f"ps_{next(_AP_COUNTER)}"
        self.layer = layer
        self.action = action
        self.status: str = "pending"
        self.result: Any = None
        self.order = order


class AutonomousPlan:
    """A multi-step autonomous execution plan."""

    __slots__ = ("plan_id", "goal", "steps", "status", "created_at",
                 "completed_at", "replan_count", "metadata")

    def __init__(self, goal: str = "") -> None:
        self.plan_id: str = f"aplan_{next(_AP_COUNTER)}"
        self.goal = goal
        self.steps: List[PlanStep] = []
        self.status: str = "created"
        self.created_at: float = time.time()
        self.completed_at: Optional[float] = None
        self.replan_count: int = 0
        self.metadata: Dict[str, Any] = {}

    def add_step(self, layer: str, action: str) -> PlanStep:
        step = PlanStep(layer, action, len(self.steps))
        self.steps.append(step)
        return step

    @property
    def progress(self) -> float:
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps if s.status == "completed")
        return round(completed / len(self.steps), 3)

    @property
    def is_complete(self) -> bool:
        return all(s.status in ("completed", "skipped") for s in self.steps)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id, "goal": self.goal,
            "total_steps": len(self.steps), "status": self.status,
            "progress": self.progress, "replan_count": self.replan_count,
        }


class AutonomousPlanner:
    """Create and manage long-term autonomous plans."""

    def __init__(self) -> None:
        self._plans: List[AutonomousPlan] = []
        self._replan_history: List[Dict[str, Any]] = []

    def create_plan(self, goal: str, steps: Optional[List[Dict[str, str]]] = None) -> AutonomousPlan:
        plan = AutonomousPlan(goal)
        if steps:
            for i, step in enumerate(steps):
                plan.add_step(step.get("layer", ""), step.get("action", ""))
        self._plans.append(plan)
        return plan

    def replan(self, plan_id: str, new_steps: List[Dict[str, str]]) -> Optional[AutonomousPlan]:
        for plan in self._plans:
            if plan.plan_id == plan_id:
                plan.steps.clear()
                for step in new_steps:
                    plan.add_step(step.get("layer", ""), step.get("action", ""))
                plan.replan_count += 1
                self._replan_history.append({
                    "plan_id": plan_id, "new_step_count": len(new_steps),
                    "time": time.time(),
                })
                return plan
        return None

    def get_plan(self, plan_id: str) -> Optional[AutonomousPlan]:
        for p in self._plans:
            if p.plan_id == plan_id:
                return p
        return None

    def get_active_plans(self) -> List[AutonomousPlan]:
        return [p for p in self._plans if p.status in ("created", "in_progress")]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_plans": len(self._plans),
            "active": len(self.get_active_plans()),
            "total_replans": len(self._replan_history),
        }
