"""base_repository.py — Base repository with CRUD."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional, TypeVar

T = TypeVar("T")


class BaseEntity:
    """Base entity for repository pattern."""
    __slots__ = ("id", "created_at", "updated_at", "metadata")
    _counter = 0

    def __init__(self) -> None:
        BaseEntity._counter += 1
        self.id: int = BaseEntity._counter
        self.created_at: float = time.time()
        self.updated_at: float = time.time()
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "created_at": self.created_at}


class BaseRepository:
    """Generic CRUD repository."""

    def __init__(self, entity_name: str) -> None:
        self._entity_name = entity_name
        self._store: Dict[int, Any] = {}
        self._auto_id = True

    def create(self, entity: Any) -> Any:
        if hasattr(entity, "id"):
            self._store[entity.id] = entity
        return entity

    def get_by_id(self, entity_id: int) -> Optional[Any]:
        return self._store.get(entity_id)

    def get_all(self) -> List[Any]:
        return list(self._store.values())

    def update(self, entity_id: int, data: Dict[str, Any]) -> Optional[Any]:
        entity = self._store.get(entity_id)
        if entity:
            for k, v in data.items():
                if hasattr(entity, k):
                    setattr(entity, k, v)
            if hasattr(entity, "updated_at"):
                entity.updated_at = time.time()
        return entity

    def delete(self, entity_id: int) -> bool:
        return self._store.pop(entity_id, None) is not None

    def count(self) -> int:
        return len(self._store)

    def exists(self, entity_id: int) -> bool:
        return entity_id in self._store

    def find(self, **kwargs: Any) -> List[Any]:
        results = []
        for entity in self._store.values():
            match = True
            for k, v in kwargs.items():
                if not hasattr(entity, k) or getattr(entity, k) != v:
                    match = False
                    break
            if match:
                results.append(entity)
        return results

    def find_one(self, **kwargs: Any) -> Optional[Any]:
        results = self.find(**kwargs)
        return results[0] if results else None

    def clear(self) -> int:
        count = len(self._store)
        self._store.clear()
        return count

    def stats(self) -> Dict[str, Any]:
        return {"entity": self._entity_name, "count": len(self._store)}
