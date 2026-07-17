"""Improvement Planner — Suggest improvements with priority and impact."""
from __future__ import annotations
import itertools
from typing import Any, Dict, List

from layers.layer09_learning.modules.learning_engine.lesson_generator import Lesson

_IMPROVEMENT_COUNTER = itertools.count(1)

PRIORITY_LEVELS = ("critical", "high", "medium", "low")
IMPACT_LEVELS = ("high", "medium", "low")


class Improvement:
    """A suggested improvement."""

    __slots__ = ("improvement_id", "title", "description", "priority",
                 "impact", "source_lesson", "category", "estimated_effort",
                 "status", "platform")

    def __init__(self, title: str = "", priority: str = "medium") -> None:
        self.improvement_id: str = f"imp_{next(_IMPROVEMENT_COUNTER)}"
        self.title = title
        self.description: str = ""
        self.priority = priority if priority in PRIORITY_LEVELS else "medium"
        self.impact: str = "medium"
        self.source_lesson: str = ""
        self.category: str = ""
        self.estimated_effort: str = "low"
        self.status: str = "suggested"
        self.platform: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "improvement_id": self.improvement_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "impact": self.impact,
            "status": self.status,
            "platform": self.platform,
        }


class ImprovementPlanner:
    """Plan improvements from lessons."""

    def __init__(self) -> None:
        self._improvements: List[Improvement] = []
        self._planning_count = 0

    def plan_from_lessons(self, lessons: List[Lesson]) -> List[Improvement]:
        new_improvements: List[Improvement] = []
        for lesson in lessons:
            imp = Improvement()
            if lesson.lesson_type == "best_practice":
                imp.title = f"Replicate: {lesson.title}"
                imp.description = f"Apply the success pattern from {lesson.platform or 'observed data'}"
                imp.priority = "high"
                imp.impact = "high"
            elif lesson.lesson_type == "mistake":
                imp.title = f"Fix: {lesson.title}"
                imp.description = f"Address recurring issue: {lesson.description[:80]}"
                imp.priority = "critical"
                imp.impact = "high"
            elif lesson.lesson_type == "warning":
                imp.title = f"Monitor: {lesson.title}"
                imp.description = lesson.description[:80]
                imp.priority = "medium"
                imp.impact = "medium"
            else:
                imp.title = f"Review: {lesson.title}"
                imp.description = lesson.description[:80]
                imp.priority = "low"
                imp.impact = "low"
            imp.source_lesson = lesson.lesson_id
            imp.platform = lesson.platform
            imp.category = lesson.category
            new_improvements.append(imp)
            self._improvements.append(imp)
        self._planning_count += 1
        return new_improvements

    def prioritize(self) -> List[Improvement]:
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return sorted(self._improvements, key=lambda i: priority_order.get(i.priority, 4))

    def get_improvements(self, priority: str = "", platform: str = "") -> List[Improvement]:
        result = self._improvements
        if priority:
            result = [i for i in result if i.priority == priority]
        if platform:
            result = [i for i in result if i.platform == platform]
        return result

    @property
    def improvement_count(self) -> int:
        return len(self._improvements)

    @property
    def planning_count(self) -> int:
        return self._planning_count
