"""audit_repository.py — Audit log repository."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.repository_layer.base_repository import BaseRepository, BaseEntity


class AuditEntity(BaseEntity):
    __slots__ = ("action", "entity_type", "entity_id", "user_id", "changes")

    def __init__(self, action: str, entity_type: str = "", entity_id: int = 0) -> None:
        super().__init__()
        self.action = action
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.user_id: int = 0
        self.changes: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({"action": self.action, "entity_type": self.entity_type,
                      "entity_id": self.entity_id})
        return base


class AuditRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("audit")

    def find_by_action(self, action: str) -> List[AuditEntity]:
        return self.find(action=action)

    def find_by_entity_type(self, entity_type: str) -> List[AuditEntity]:
        return self.find(entity_type=entity_type)

    def find_by_user(self, user_id: int) -> List[AuditEntity]:
        return self.find(user_id=user_id)
