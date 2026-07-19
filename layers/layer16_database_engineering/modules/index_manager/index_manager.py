"""IndexManager — manage database indexes for query optimization."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from enum import Enum


class IndexType(str, Enum):
    HASH = "hash"; BTREE = "btree"; GIN = "gin"; GIST = "gist"


class IndexInfo:
    __slots__ = ("index_name", "table_name", "columns", "index_type",
                 "unique", "created_at", "metadata")

    def __init__(self, index_name: str, table_name: str, columns: List[str],
                 index_type: IndexType = IndexType.BTREE,
                 unique: bool = False) -> None:
        self.index_name = index_name
        self.table_name = table_name
        self.columns = columns
        self.index_type = index_type
        self.unique = unique
        self.created_at = 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"index_name": self.index_name, "table_name": self.table_name,
                "columns": self.columns, "type": self.index_type.value,
                "unique": self.unique}


class IndexManager:
    def __init__(self) -> None:
        self._indexes: Dict[str, IndexInfo] = {}

    def create_index(self, index_name: str, table_name: str,
                     columns: List[str], index_type: IndexType = IndexType.BTREE,
                     unique: bool = False) -> IndexInfo:
        info = IndexInfo(index_name, table_name, columns, index_type, unique)
        self._indexes[index_name] = info
        return info

    def drop_index(self, index_name: str) -> bool:
        if index_name in self._indexes:
            del self._indexes[index_name]
            return True
        return False

    def get_index(self, index_name: str) -> Optional[IndexInfo]:
        return self._indexes.get(index_name)

    def list_indexes(self, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        if table_name:
            return [i.to_dict() for i in self._indexes.values() if i.table_name == table_name]
        return [i.to_dict() for i in self._indexes.values()]

    def count(self) -> int:
        return len(self._indexes)
