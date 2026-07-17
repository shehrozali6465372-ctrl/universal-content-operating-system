"""GoalDecomposer — Break large goals into small tasks."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_GD_COUNTER = itertools.count(1)


class Milestone:
    """A milestone in goal decomposition."""

    __slots__ = ("milestone_id", "name", "tasks", "status", "priority",
                 "dependencies")

    def __init__(self, name: str = "", priority: int = 0) -> None:
        self.milestone_id: str = f"ms_{next(_GD_COUNTER)}"
        self.name = name
        self.tasks: List[Dict[str, str]] = []
        self.status: str = "pending"
        self.priority = priority
        self.dependencies: List[str] = []

    def add_task(self, layer: str, action: str, description: str = "") -> Dict[str, str]:
        task = {"layer": layer, "action": action, "description": description}
        self.tasks.append(task)
        return task

    def to_dict(self) -> Dict[str, Any]:
        return {
            "milestone_id": self.milestone_id, "name": self.name,
            "task_count": len(self.tasks), "priority": self.priority,
        }


class GoalDecomposition:
    """Result of decomposing a goal."""

    __slots__ = ("decomposition_id", "goal", "milestones", "created_at")

    def __init__(self, goal: str = "") -> None:
        self.decomposition_id: str = f"gd_{next(_GD_COUNTER)}"
        self.goal = goal
        self.milestones: List[Milestone] = []
        self.created_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decomposition_id": self.decomposition_id,
            "goal": self.goal, "milestone_count": len(self.milestones),
        }


class GoalDecomposer:
    """Decompose large goals into milestones and tasks."""

    DEFAULT_DECOMPOSITIONS = {
        "grow_audience": [
            ("Research Phase", [("layer02_research", "trend_analysis", "Identify trends"),
                                ("layer03_intelligence", "content_understanding", "Analyze audience")]),
            ("Content Phase", [("layer04_writing", "draft", "Create content"),
                                ("layer05_image", "image_plan", "Design visuals")]),
            ("Quality Phase", [("layer06_quality", "quality_check", "Quality assurance")]),
            ("Publish Phase", [("layer07_publishing", "publish", "Publish content")]),
            ("Learn Phase", [("layer08_analytics", "analytics", "Analyze results"),
                              ("layer09_learning", "learn", "Optimize strategy")]),
        ],
        "improve_engagement": [
            ("Analyze", [("layer08_analytics", "analytics", "Analyze current engagement")]),
            ("Optimize", [("layer04_writing", "draft", "Write engaging content"),
                           ("layer06_quality", "quality_check", "Quality check")]),
            ("Publish & Learn", [("layer07_publishing", "publish", "Publish"),
                                  ("layer09_learning", "learn", "Learn from results")]),
        ],
    }

    def __init__(self) -> None:
        self._decompositions: List[GoalDecomposition] = []

    def decompose(self, goal: str, goal_type: str = "",
                  custom_milestones: Optional[List[Dict[str, Any]]] = None) -> GoalDecomposition:
        result = GoalDecomposition(goal)
        templates = custom_milestones or self.DEFAULT_DECOMPOSITIONS.get(goal_type, [])

        for template in templates:
            if isinstance(template, tuple) and len(template) >= 2:
                ms = Milestone(template[0])
                for task_data in template[1]:
                    if isinstance(task_data, tuple) and len(task_data) >= 2:
                        ms.add_task(task_data[0], task_data[1],
                                   task_data[2] if len(task_data) > 2 else "")
                result.milestones.append(ms)

        self._decompositions.append(result)
        return result

    def add_milestone(self, decomposition_id: str, name: str,
                      tasks: Optional[List[Dict[str, str]]] = None) -> Optional[Milestone]:
        for d in self._decompositions:
            if d.decomposition_id == decomposition_id:
                ms = Milestone(name)
                if tasks:
                    for t in tasks:
                        ms.add_task(t.get("layer", ""), t.get("action", ""), t.get("description", ""))
                d.milestones.append(ms)
                return ms
        return None

    def get_decomposition(self, decomposition_id: str) -> Optional[GoalDecomposition]:
        for d in self._decompositions:
            if d.decomposition_id == decomposition_id:
                return d
        return None

    def get_stats(self) -> Dict[str, Any]:
        total_milestones = sum(len(d.milestones) for d in self._decompositions)
        total_tasks = sum(sum(len(m.tasks) for m in d.milestones) for d in self._decompositions)
        return {"total_decompositions": len(self._decompositions),
                "total_milestones": total_milestones, "total_tasks": total_tasks}
