"""Goal Manager — AI objective management."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_GM_COUNTER = itertools.count(1)

GOAL_STATUSES = ("active", "completed", "cancelled", "paused")
GOAL_PRIORITIES = ("critical", "high", "normal", "low")


class Goal:
    """An AI objective."""

    __slots__ = ("goal_id", "name", "description", "status", "priority",
                 "target_metric", "target_value", "current_value",
                 "created_at", "completed_at", "metadata")

    def __init__(self, name: str = "", description: str = "") -> None:
        self.goal_id: str = f"goal_{next(_GM_COUNTER)}"
        self.name = name
        self.description = description
        self.status: str = "active"
        self.priority: str = "normal"
        self.target_metric: str = ""
        self.target_value: float = 0.0
        self.current_value: float = 0.0
        self.created_at: float = time.time()
        self.completed_at: Optional[float] = None
        self.metadata: Dict[str, Any] = {}

    @property
    def progress(self) -> float:
        if self.target_value <= 0:
            return 0.0
        return min(1.0, self.current_value / self.target_value)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id, "name": self.name,
            "status": self.status, "priority": self.priority,
            "progress": round(self.progress, 3),
        }


class GoalManager:
    """Manage AI objectives and priorities."""

    def __init__(self) -> None:
        self._goals: List[Goal] = []

    def create_goal(self, name: str, description: str = "",
                    priority: str = "normal", target_metric: str = "",
                    target_value: float = 0.0) -> Goal:
        goal = Goal(name, description)
        goal.priority = priority if priority in GOAL_PRIORITIES else "normal"
        goal.target_metric = target_metric
        goal.target_value = target_value
        self._goals.append(goal)
        return goal

    def update_goal(self, goal_id: str, **kwargs) -> Optional[Goal]:
        for goal in self._goals:
            if goal.goal_id == goal_id:
                for k, v in kwargs.items():
                    if hasattr(goal, k):
                        setattr(goal, k, v)
                return goal
        return None

    def complete_goal(self, goal_id: str) -> Optional[Goal]:
        goal = self.update_goal(goal_id, status="completed", completed_at=time.time())
        return goal

    def cancel_goal(self, goal_id: str) -> Optional[Goal]:
        return self.update_goal(goal_id, status="cancelled")

    def get_active_goals(self) -> List[Goal]:
        return [g for g in self._goals if g.status == "active"]

    def get_by_priority(self, priority: str) -> List[Goal]:
        return [g for g in self._goals if g.priority == priority]

    def prioritize_goals(self) -> List[Goal]:
        order = {"critical": 0, "high": 1, "normal": 2, "low": 3}
        return sorted(self._goals, key=lambda g: order.get(g.priority, 2))

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        for g in self._goals:
            if g.goal_id == goal_id:
                return g
        return None

    def get_stats(self) -> Dict[str, Any]:
        active = sum(1 for g in self._goals if g.status == "active")
        completed = sum(1 for g in self._goals if g.status == "completed")
        return {"total": len(self._goals), "active": active, "completed": completed}
