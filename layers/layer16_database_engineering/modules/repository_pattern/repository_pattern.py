"""Repository Pattern — generic data access abstraction."""
from __future__ import annotations
import time
import uuid
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")


class BaseRepository:
    def __init__(self, entity_name: str) -> None:
        self.entity_name = entity_name
        self._store: Dict[str, Dict[str, Any]] = {}
        self._index: Dict[str, Dict[str, List[str]]] = {}

    def _generate_id(self) -> str:
        return f"{self.entity_name}_{str(uuid.uuid4())[:8]}"

    def add(self, data: Dict[str, Any], entity_id: Optional[str] = None) -> Dict[str, Any]:
        eid = entity_id or self._generate_id()
        record = {"id": eid, **data, "_created_at": time.time(), "_updated_at": time.time()}
        self._store[eid] = record
        self._update_index(eid, data)
        return record

    def get(self, entity_id: str) -> Optional[Dict[str, Any]]:
        return self._store.get(entity_id)

    def update(self, entity_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if entity_id in self._store:
            self._store[entity_id].update(data)
            self._store[entity_id]["_updated_at"] = time.time()
            return self._store[entity_id]
        return None

    def delete(self, entity_id: str) -> bool:
        if entity_id in self._store:
            del self._store[entity_id]
            return True
        return False

    def list_all(self) -> List[Dict[str, Any]]:
        return list(self._store.values())

    def find_by(self, field: str, value: Any) -> List[Dict[str, Any]]:
        return [r for r in self._store.values() if r.get(field) == value]

    def find_one_by(self, field: str, value: Any) -> Optional[Dict[str, Any]]:
        for r in self._store.values():
            if r.get(field) == value:
                return r
        return None

    def count(self) -> int:
        return len(self._store)

    def exists(self, entity_id: str) -> bool:
        return entity_id in self._store

    def find_by_index(self, index_name: str, value: Any) -> List[Dict[str, Any]]:
        ids = self._index.get(index_name, {}).get(str(value), [])
        return [self._store[eid] for eid in ids if eid in self._store]

    def create_index(self, field: str) -> None:
        self._index[field] = {}
        for eid, record in self._store.items():
            val = str(record.get(field, ""))
            self._index[field].setdefault(val, []).append(eid)

    def _update_index(self, eid: str, data: Dict[str, Any]) -> None:
        for field, idx in self._index.items():
            val = str(data.get(field, ""))
            idx.setdefault(val, []).append(eid)

    def clear(self) -> int:
        count = len(self._store)
        self._store.clear()
        self._index.clear()
        return count

    def bulk_add(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.add(item) for item in items]
