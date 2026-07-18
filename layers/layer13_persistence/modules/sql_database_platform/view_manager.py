"""view_manager.py — Database view management."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class DatabaseView:
    """Database view definition."""
    __slots__ = ("name", "sql", "materialized", "created_at")
    _counter = 0

    def __init__(self, name: str, sql: str, materialized: bool = False) -> None:
        DatabaseView._counter += 1
        self.name = name
        self.sql = sql
        self.materialized = materialized
        import time
        self.created_at: float = time.time()


class ViewManager:
    """Manages database views."""

    def __init__(self) -> None:
        self._views: Dict[str, DatabaseView] = {}

    def create(self, view: DatabaseView) -> None:
        self._views[view.name] = view

    def drop(self, name: str) -> bool:
        return self._views.pop(name, None) is not None

    def get(self, name: str) -> Optional[DatabaseView]:
        return self._views.get(name)

    def list_all(self) -> List[DatabaseView]:
        return list(self._views.values())

    def list_materialized(self) -> List[DatabaseView]:
        return [v for v in self._views.values() if v.materialized]

    def stats(self) -> Dict[str, Any]:
        return {"views": len(self._views),
                "materialized": len(self.list_materialized())}
