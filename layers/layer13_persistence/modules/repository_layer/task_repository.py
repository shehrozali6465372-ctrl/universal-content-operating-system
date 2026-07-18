"""task_repository.py — Task repository."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.repository_layer.base_repository import BaseRepository, BaseEntity


class TaskEntity(BaseEntity):
    __slots__ = ("title", "status", "assigned_to", "priority", "due_date")

    def __init__(self, title: str, assigned_to: int = 0) -> None:
        super().__init__()
        self.title = title
        self.status: str = "pending"
        self.assigned_to = assigned_to
        self.priority: int = 5
        self.due_date: str = ""

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({"title": self.title, "status": self.status,
                      "assigned_to": self.assigned_to})
        return base


class TaskRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("task")

    def find_pending(self) -> List[TaskEntity]:
        return self.find(status="pending")

    def find_by_assignee(self, user_id: int) -> List[TaskEntity]:
        return self.find(assigned_to=user_id)
