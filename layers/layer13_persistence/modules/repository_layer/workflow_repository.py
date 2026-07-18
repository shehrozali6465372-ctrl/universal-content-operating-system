"""workflow_repository.py — Workflow repository."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.repository_layer.base_repository import BaseRepository, BaseEntity


class WorkflowEntity(BaseEntity):
    __slots__ = ("name", "steps", "status", "current_step")

    def __init__(self, name: str, steps: List[str] = None) -> None:
        super().__init__()
        self.name = name
        self.steps = steps or []
        self.status: str = "pending"
        self.current_step: int = 0

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({"name": self.name, "status": self.status,
                      "current_step": self.current_step, "steps": len(self.steps)})
        return base


class WorkflowRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("workflow")

    def find_running(self) -> List[WorkflowEntity]:
        return self.find(status="running")

    def find_completed(self) -> List[WorkflowEntity]:
        return self.find(status="completed")
