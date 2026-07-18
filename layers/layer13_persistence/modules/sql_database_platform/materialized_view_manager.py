"""materialized_view_manager.py — Materialized view management."""
from __future__ import annotations
import time
from typing import Dict, List


class MaterializedView:
    """Materialized view definition."""
    __slots__ = ("name", "query", "refresh_interval", "last_refreshed", "size_bytes")
    _counter = 0

    def __init__(self, name: str, query: str, refresh_interval: float = 3600.0) -> None:
        MaterializedView._counter += 1
        self.name = name
        self.query = query
        self.refresh_interval = refresh_interval
        self.last_refreshed: float = 0.0
        self.size_bytes: int = 0


class MaterializedViewManager:
    """Manages materialized views."""

    def __init__(self) -> None:
        self._views: Dict[str, MaterializedView] = {}

    def create(self, view: MaterializedView) -> None:
        self._views[view.name] = view

    def refresh(self, name: str) -> bool:
        view = self._views.get(name)
        if view:
            view.last_refreshed = time.time()
            return True
        return False

    def needs_refresh(self, name: str) -> bool:
        view = self._views.get(name)
        if not view:
            return False
        return (time.time() - view.last_refreshed) > view.refresh_interval

    def drop(self, name: str) -> bool:
        return self._views.pop(name, None) is not None

    def list_all(self) -> List[MaterializedView]:
        return list(self._views.values())
