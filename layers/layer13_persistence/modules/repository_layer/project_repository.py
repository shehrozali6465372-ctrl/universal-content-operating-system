"""project_repository.py — Project repository."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.repository_layer.base_repository import BaseRepository, BaseEntity


class ProjectEntity(BaseEntity):
    __slots__ = ("name", "description", "status", "owner_id")

    def __init__(self, name: str, description: str = "", owner_id: int = 0) -> None:
        super().__init__()
        self.name = name
        self.description = description
        self.status = "active"
        self.owner_id = owner_id

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({"name": self.name, "status": self.status})
        return base


class ProjectRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("project")

    def find_by_owner(self, owner_id: int) -> List[ProjectEntity]:
        return self.find(owner_id=owner_id)

    def find_by_status(self, status: str) -> List[ProjectEntity]:
        return self.find(status=status)
