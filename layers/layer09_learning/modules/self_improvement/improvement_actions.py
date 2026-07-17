"""Improvement Actions — Define and manage improvement actions."""
from __future__ import annotations
import itertools
from typing import Any, Dict, List

_IA_COUNTER = itertools.count(1)

ACTION_TYPES = ("fix", "optimize", "experiment", "calibrate", "learn")
ACTION_STATUSES = ("planned", "in_progress", "completed", "failed", "skipped")
ACTION_PRIORITIES = ("critical", "high", "medium", "low")


class ImprovementAction:
    """A single improvement action to address a weakness or mistake."""

    __slots__ = ("action_id", "action_type", "priority", "status",
                 "title", "description", "target_area", "expected_impact",
                 "actual_impact", "source_id", "tags")

    def __init__(self, action_type: str = "fix", priority: str = "medium") -> None:
        self.action_id: str = f"ima_{next(_IA_COUNTER)}"
        self.action_type = action_type if action_type in ACTION_TYPES else "fix"
        self.priority = priority if priority in ACTION_PRIORITIES else "medium"
        self.status: str = "planned"
        self.title: str = ""
        self.description: str = ""
        self.target_area: str = ""
        self.expected_impact: float = 0.5
        self.actual_impact: float = 0.0
        self.source_id: str = ""
        self.tags: List[str] = []

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    @property
    def impact_delta(self) -> float:
        return round(self.actual_impact - self.expected_impact, 3)

    def complete(self, actual_impact: float = 0.0) -> None:
        self.status = "completed"
        self.actual_impact = actual_impact

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "priority": self.priority,
            "status": self.status,
            "title": self.title,
            "target_area": self.target_area,
            "expected_impact": round(self.expected_impact, 3),
            "actual_impact": round(self.actual_impact, 3),
        }


class ImprovementActionManager:
    """Manage the lifecycle of improvement actions."""

    def __init__(self) -> None:
        self._actions: List[ImprovementAction] = []

    def create(self, action_type: str, priority: str, title: str,
               target_area: str = "", source_id: str = "") -> ImprovementAction:
        action = ImprovementAction(action_type, priority)
        action.title = title
        action.target_area = target_area
        action.source_id = source_id
        self._actions.append(action)
        return action

    def create_from_mistakes(self, mistakes: List[Dict[str, Any]]) -> List[ImprovementAction]:
        actions = []
        for m in mistakes:
            severity = m.get("severity", "medium")
            priority = severity if severity in ACTION_PRIORITIES else "medium"
            action = self.create(
                "fix", priority,
                title=m.get("description", "Fix mistake"),
                target_area=m.get("category", ""),
                source_id=m.get("mistake_id", ""),
            )
            action.description = m.get("suggestion", "")
            actions.append(action)
        return actions

    def complete_action(self, action_id: str, actual_impact: float = 0.0) -> bool:
        for a in self._actions:
            if a.action_id == action_id:
                a.complete(actual_impact)
                return True
        return False

    def get_actions(self, status: str = "", action_type: str = "",
                    priority: str = "") -> List[ImprovementAction]:
        result = self._actions
        if status:
            result = [a for a in result if a.status == status]
        if action_type:
            result = [a for a in result if a.action_type == action_type]
        if priority:
            result = [a for a in result if a.priority == priority]
        return result

    def get_completed(self) -> List[ImprovementAction]:
        return self.get_actions(status="completed")

    @property
    def action_count(self) -> int:
        return len(self._actions)
