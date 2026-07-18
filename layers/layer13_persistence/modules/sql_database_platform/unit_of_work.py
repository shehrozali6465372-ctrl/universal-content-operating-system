"""unit_of_work.py — Unit of Work pattern."""
from __future__ import annotations
from typing import Any, Dict, List


class UnitOfWork:
    """Unit of Work for batching operations."""

    def __init__(self) -> None:
        self._operations: List[Dict[str, Any]] = []
        self._new_entities: List[Any] = []
        self._dirty_entities: List[Any] = []
        self._removed_entities: List[Any] = []
        self._committed: bool = False

    def register_new(self, entity: Any) -> None:
        self._new_entities.append(entity)

    def register_dirty(self, entity: Any) -> None:
        self._dirty_entities.append(entity)

    def register_removed(self, entity: Any) -> None:
        self._removed_entities.append(entity)

    def commit(self) -> bool:
        self._committed = True
        return True

    def rollback(self) -> bool:
        self._new_entities.clear()
        self._dirty_entities.clear()
        self._removed_entities.clear()
        return True

    def is_committed(self) -> bool:
        return self._committed

    def get_pending(self) -> Dict[str, int]:
        return {"new": len(self._new_entities), "dirty": len(self._dirty_entities),
                "removed": len(self._removed_entities)}

    def clear(self) -> None:
        self._new_entities.clear()
        self._dirty_entities.clear()
        self._removed_entities.clear()
        self._committed = False
