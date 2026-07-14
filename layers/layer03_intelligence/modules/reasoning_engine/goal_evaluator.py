"""Goal Evaluator - Evaluates progress toward goals."""
from __future__ import annotations
import time
from typing import Dict, List, Optional


class Goal:
    """A measurable goal."""
    __slots__ = ("name", "target", "current", "unit", "deadline", "created_at", "priority")

    def __init__(self, name: str = "", target: float = 1.0, current: float = 0.0,
                 unit: str = "", priority: str = "medium"):
        self.name = name
        self.target = target
        self.current = current
        self.unit = unit
        self.deadline = 0.0
        self.created_at = time.time()
        self.priority = priority

    @property
    def progress(self) -> float:
        return min(1.0, self.current / max(self.target, 0.001))

    @property
    def achieved(self) -> bool:
        return self.current >= self.target

    def to_dict(self) -> Dict:
        return {"name": self.name, "target": self.target, "current": round(self.current, 3),
                "progress": round(self.progress, 3), "achieved": self.achieved,
                "unit": self.unit, "priority": self.priority}


class GoalEvaluation:
    """Evaluation of a goal's status."""
    __slots__ = ("goal", "status", "on_track", "estimated_completion", "recommendations")

    def __init__(self) -> None:
        self.goal: Optional[Goal] = None
        self.status = "unknown"
        self.on_track = True
        self.estimated_completion = ""
        self.recommendations: List[str] = []

    def to_dict(self) -> Dict:
        return {
            "goal": self.goal.to_dict() if self.goal else None,
            "status": self.status, "on_track": self.on_track,
            "estimated_completion": self.estimated_completion,
            "recommendations": list(self.recommendations),
        }


class GoalEvaluator:
    """Evaluates progress toward goals."""

    def __init__(self) -> None:
        self._goals: List[Goal] = []

    def add_goal(self, goal: Goal) -> None:
        self._goals.append(goal)

    def evaluate(self, goal: Goal) -> GoalEvaluation:
        result = GoalEvaluation()
        result.goal = goal

        if goal.achieved:
            result.status = "achieved"
            result.recommendations.append(f"Goal '{goal.name}' achieved!")
        elif goal.progress >= 0.7:
            result.status = "on_track"
            result.recommendations.append(f"Progress {goal.progress:.0%} - nearly there")
        elif goal.progress >= 0.3:
            result.status = "in_progress"
            result.recommendations.append(f"Progress {goal.progress:.0%} - need more effort")
        else:
            result.status = "behind"
            result.on_track = False
            result.recommendations.append(f"Progress {goal.progress:.0%} - consider increasing effort")

        return result

    def evaluate_all(self) -> List[GoalEvaluation]:
        return [self.evaluate(g) for g in self._goals]

    def get_overall_progress(self) -> float:
        if not self._goals:
            return 0.0
        return sum(g.progress for g in self._goals) / len(self._goals)

    def count(self) -> int:
        return len(self._goals)
