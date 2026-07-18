"""schema_manager.py — Database schema management."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class TableSchema:
    """Schema definition for a table."""
    __slots__ = ("name", "columns", "primary_key", "indexes", "created_at")
    _counter = 0

    def __init__(self, name: str) -> None:
        TableSchema._counter += 1
        self.name = name
        self.columns: Dict[str, str] = {}
        self.primary_key: str = ""
        self.indexes: List[str] = []
        self.created_at: float = time.time()

    def add_column(self, name: str, col_type: str, nullable: bool = True) -> None:
        self.columns[name] = f"{col_type}{' NOT NULL' if not nullable else ''}"

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "columns": dict(self.columns),
                "primary_key": self.primary_key, "indexes": self.indexes}


class SchemaManager:
    """Manages database schemas."""

    def __init__(self) -> None:
        self._schemas: Dict[str, TableSchema] = {}
        self._history: List[Dict[str, Any]] = []

    def create_table(self, schema: TableSchema) -> bool:
        self._schemas[schema.name] = schema
        self._history.append({"action": "create_table", "table": schema.name,
                               "time": time.time()})
        return True

    def drop_table(self, name: str) -> bool:
        if name in self._schemas:
            del self._schemas[name]
            self._history.append({"action": "drop_table", "table": name,
                                   "time": time.time()})
            return True
        return False

    def alter_table(self, name: str, add_columns: Dict[str, str] = None) -> bool:
        schema = self._schemas.get(name)
        if schema and add_columns:
            for col, col_type in add_columns.items():
                schema.columns[col] = col_type
            self._history.append({"action": "alter_table", "table": name,
                                   "time": time.time()})
            return True
        return False

    def get_schema(self, name: str) -> Optional[TableSchema]:
        return self._schemas.get(name)

    def list_tables(self) -> List[str]:
        return list(self._schemas.keys())

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
