"""persistence_version.py — Persistence schema versioning."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class PersistenceVersion:
    """Tracks persistence schema versions."""

    __slots__ = ("_current_version", "_history", "_migrations")

    def __init__(self) -> None:
        self._current_version: str = "1.0.0"
        self._history: List[Dict[str, Any]] = [{"version": "1.0.0", "applied_at": time.time(),
                                                  "description": "Initial schema"}]
        self._migrations: List[Dict[str, Any]] = []

    def get_current(self) -> str:
        return self._current_version

    def upgrade(self, new_version: str, description: str = "") -> bool:
        self._current_version = new_version
        self._history.append({"version": new_version, "applied_at": time.time(),
                               "description": description})
        return True

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)

    def register_migration(self, from_version: str, to_version: str,
                           description: str = "") -> None:
        self._migrations.append({"from": from_version, "to": to_version,
                                  "description": description})

    def get_migrations(self) -> List[Dict[str, Any]]:
        return list(self._migrations)

    def to_dict(self) -> Dict[str, Any]:
        return {"current_version": self._current_version,
                "history": list(self._history),
                "migrations": len(self._migrations)}
