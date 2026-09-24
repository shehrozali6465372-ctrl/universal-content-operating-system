"""Layer 1 memory contract adapter backed by Layer 13 PostgreSQL.

This adapter is the production boundary used when Layer 1 requests its memory
service. Layer 13 owns the PostgreSQL pool and therefore owns connection
lifecycle; close() is intentionally a no-op.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class Layer1PostgreSQLMemoryBackend:
    """Expose the Layer 1 memory persistence contract over PostgreSQL."""

    def __init__(self, postgres_manager):
        if postgres_manager is None or postgres_manager.memory is None:
            raise RuntimeError("Layer 13 PostgreSQL memory repository is not initialized")
        self._postgres = postgres_manager
        self._repository = postgres_manager.memory

    def health_check(self) -> Dict[str, Any]:
        return self._postgres.health_check()

    def save(
        self,
        level: str,
        category: str,
        key: str,
        value: str,
        tags: str = "",
        importance: float = 0.5,
    ) -> int:
        return self._repository.save(level, category, key, value, tags, importance)

    def load(self, level: str, category: str = "", key: str = "") -> List[Dict[str, Any]]:
        if category or key:
            rows = self._repository.get_by_level(level)
            if category:
                rows = [row for row in rows if row.get("category") == category]
            if key:
                rows = [row for row in rows if row.get("key") == key]
            return rows
        return self._repository.get_by_level(level)

    def search(
        self,
        level: str,
        category: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        return self._repository.search(level, category, limit)

    def increment_access(self, entry_id: int) -> None:
        self._repository.increment_access(entry_id)

    def get_by_level(self, level: str) -> List[Dict[str, Any]]:
        return self._repository.get_by_level(level)

    def delete_by_level(self, level: str) -> int:
        return self._repository.delete_by_level(level)

    def close(self) -> None:
        """Layer 13 PostgreSQLManager owns the shared pool lifecycle."""
        return None
