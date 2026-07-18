"""entity_manager.py — Universal entity management."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer13_persistence.modules.repository_layer.base_repository import BaseEntity


class EntityManager:
    """Manages entities across repositories."""

    def __init__(self) -> None:
        self._repositories: Dict[str, Any] = {}
        self._entities: Dict[int, BaseEntity] = {}

    def register(self, name: str, repository: Any) -> None:
        self._repositories[name] = repository

    def get_repository(self, name: str) -> Any:
        return self._repositories.get(name)

    def find(self, entity_id: int) -> Optional[BaseEntity]:
        return self._entities.get(entity_id)

    def find_by_type(self, entity_type: str) -> List[BaseEntity]:
        return [e for e in self._entities.values()
                if type(e).__name__ == entity_type]

    def count(self) -> int:
        return len(self._entities)

    def stats(self) -> Dict[str, Any]:
        return {"repositories": len(self._repositories), "entities": len(self._entities)}
