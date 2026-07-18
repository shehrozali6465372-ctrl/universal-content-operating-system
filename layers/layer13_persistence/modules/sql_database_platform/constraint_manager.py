"""constraint_manager.py — Database constraint management."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class DatabaseConstraint:
    """Database constraint definition."""
    __slots__ = ("name", "table", "constraint_type", "columns", "definition")
    _counter = 0

    def __init__(self, name: str, table: str, constraint_type: str,
                 columns: List[str]) -> None:
        DatabaseConstraint._counter += 1
        self.name = name
        self.table = table
        self.constraint_type = constraint_type
        self.columns = columns
        self.definition: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "table": self.table, "type": self.constraint_type,
                "columns": self.columns}


class ConstraintManager:
    """Manages database constraints."""

    def __init__(self) -> None:
        self._constraints: Dict[str, DatabaseConstraint] = {}

    def add(self, constraint: DatabaseConstraint) -> None:
        self._constraints[constraint.name] = constraint

    def remove(self, name: str) -> bool:
        return self._constraints.pop(name, None) is not None

    def get(self, name: str) -> Optional[DatabaseConstraint]:
        return self._constraints.get(name)

    def get_for_table(self, table: str) -> List[DatabaseConstraint]:
        return [c for c in self._constraints.values() if c.table == table]

    def list_all(self) -> List[DatabaseConstraint]:
        return list(self._constraints.values())

    def stats(self) -> Dict[str, Any]:
        types = {}
        for c in self._constraints.values():
            types[c.constraint_type] = types.get(c.constraint_type, 0) + 1
        return {"total": len(self._constraints), "by_type": types}
