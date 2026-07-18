"""migration_coordinator.py — Migration coordination."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class MigrationCoordinator:
    """Coordinates migrations across all stores."""

    def __init__(self) -> None:
        self._migrations: Dict[str, List[Dict[str, Any]]] = {}
        self._applied: List[Dict[str, Any]] = []

    def register_migration(self, store_name: str, version: str, sql: str) -> None:
        if store_name not in self._migrations:
            self._migrations[store_name] = []
        self._migrations[store_name].append({"version": version, "sql": sql,
                                               "applied": False})

    def apply_pending(self, store_name: str) -> int:
        migrations = self._migrations.get(store_name, [])
        count = 0
        for m in migrations:
            if not m["applied"]:
                m["applied"] = True
                m["applied_at"] = time.time()
                self._applied.append({**m, "store": store_name})
                count += 1
        return count

    def get_pending(self, store_name: str) -> List[Dict[str, Any]]:
        return [m for m in self._migrations.get(store_name, []) if not m["applied"]]

    def get_applied(self) -> List[Dict[str, Any]]:
        return list(self._applied)

    def stats(self) -> Dict[str, Any]:
        total = sum(len(m) for m in self._migrations.values())
        return {"total_migrations": total, "applied": len(self._applied)}
