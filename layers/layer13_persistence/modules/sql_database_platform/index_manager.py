"""index_manager.py — Database index management."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class DatabaseIndex:
    """Database index definition."""
    __slots__ = ("index_name", "table_name", "columns", "unique", "created_at")

    def __init__(self, index_name: str, table_name: str, columns: List[str],
                 unique: bool = False) -> None:
        self.index_name = index_name
        self.table_name = table_name
        self.columns = columns
        self.unique = unique
        self.created_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.index_name, "table": self.table_name,
                "columns": self.columns, "unique": self.unique}


class IndexManager:
    """Manages database indexes."""

    def __init__(self) -> None:
        self._indexes: Dict[str, DatabaseIndex] = {}

    def create_index(self, index: DatabaseIndex) -> bool:
        self._indexes[index.index_name] = index
        return True

    def drop_index(self, name: str) -> bool:
        return self._indexes.pop(name, None) is not None

    def get_index(self, name: str) -> Optional[DatabaseIndex]:
        return self._indexes.get(name)

    def get_indexes_for_table(self, table: str) -> List[DatabaseIndex]:
        return [i for i in self._indexes.values() if i.table_name == table]

    def list_all(self) -> List[DatabaseIndex]:
        return list(self._indexes.values())

    def stats(self) -> Dict[str, Any]:
        tables = {}
        for i in self._indexes.values():
            tables[i.table_name] = tables.get(i.table_name, 0) + 1
        return {"total": len(self._indexes), "by_table": tables}
