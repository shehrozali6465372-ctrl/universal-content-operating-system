"""MigrationManager — explicit, executable migration lifecycle."""
from __future__ import annotations
import itertools
import time
from typing import Any, Callable, Dict, List, Optional

_MM_COUNTER = itertools.count(1)


class Migration:
    def __init__(self, from_version: str, to_version: str,
                 apply_func: Optional[Callable[[], None]] = None,
                 rollback_func: Optional[Callable[[], None]] = None) -> None:
        self.migration_id = f"mig_{next(_MM_COUNTER)}"
        self.from_version = from_version
        self.to_version = to_version
        self.description = ""
        self.status = "pending"
        self.applied_at: Optional[float] = None
        self.apply_func = apply_func
        self.rollback_func = rollback_func

    def to_dict(self) -> Dict[str, Any]:
        return {"migration_id": self.migration_id, "from": self.from_version,
                "to": self.to_version, "status": self.status}


class MigrationManager:
    """Register migrations whose forward/rollback actions are explicit."""

    def __init__(self) -> None:
        self._migrations: List[Migration] = []

    def register(self, from_version: str, to_version: str,
                 description: str = "",
                 apply_func: Optional[Callable[[], None]] = None,
                 rollback_func: Optional[Callable[[], None]] = None) -> Migration:
        if not from_version or not to_version or from_version == to_version:
            raise ValueError("valid distinct versions are required")
        migration = Migration(from_version, to_version, apply_func, rollback_func)
        migration.description = description
        self._migrations.append(migration)
        return migration

    def apply(self, migration_id: str) -> bool:
        migration = self._find(migration_id)
        if migration is None or migration.status != "pending" or migration.apply_func is None:
            return False
        try:
            migration.apply_func()
        except Exception:
            migration.status = "failed"
            return False
        migration.status = "applied"
        migration.applied_at = time.time()
        return True

    def rollback(self, migration_id: str) -> bool:
        migration = self._find(migration_id)
        if migration is None or migration.status != "applied" or migration.rollback_func is None:
            return False
        try:
            migration.rollback_func()
        except Exception:
            return False
        migration.status = "rolled_back"
        return True

    def _find(self, migration_id: str) -> Optional[Migration]:
        return next((migration for migration in self._migrations
                     if migration.migration_id == migration_id), None)

    def get_pending(self) -> List[Migration]:
        return [m for m in self._migrations if m.status == "pending"]

    def get_applied(self) -> List[Migration]:
        return [m for m in self._migrations if m.status == "applied"]

    def get_all(self) -> List[Migration]:
        return list(self._migrations)

    def get_stats(self) -> Dict[str, Any]:
        statuses: Dict[str, int] = {}
        for migration in self._migrations:
            statuses[migration.status] = statuses.get(migration.status, 0) + 1
        return {"total": len(self._migrations), "by_status": statuses}
