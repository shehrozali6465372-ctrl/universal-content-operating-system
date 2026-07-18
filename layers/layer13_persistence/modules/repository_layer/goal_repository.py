"""goal_repository.py — Goal repository."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.repository_layer.base_repository import BaseRepository, BaseEntity


class GoalEntity(BaseEntity):
    __slots__ = ("title", "description", "status", "priority", "progress")

    def __init__(self, title: str, description: str = "", priority: int = 5) -> None:
        super().__init__()
        self.title = title
        self.description = description
        self.status: str = "active"
        self.priority = priority
        self.progress: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({"title": self.title, "status": self.status,
                      "priority": self.priority, "progress": self.progress})
        return base


class GoalRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("goal")

    def find_active(self) -> List[GoalEntity]:
        return self.find(status="active")

    def find_completed(self) -> List[GoalEntity]:
        return self.find(status="completed")

    def find_by_priority(self, min_priority: int = 5) -> List[GoalEntity]:
        return [e for e in self._store.values() if e.priority >= min_priority]
