"""MigrationManager — Version upgrades, schema migrations, plugin upgrades."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_MM_COUNTER = itertools.count(1)


class Migration:
    """A migration step."""

    __slots__ = ("migration_id", "from_version", "to_version", "description",
                 "status", "applied_at")

    def __init__(self, from_version: str = "", to_version: str = "") -> None:
        self.migration_id: str = f"mig_{next(_MM_COUNTER)}"
        self.from_version = from_version
        self.to_version = to_version
        self.description: str = ""
        self.status: str = "pending"
        self.applied_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"migration_id": self.migration_id, "from": self.from_version,
                "to": self.to_version, "status": self.status}


class MigrationManager:
    """Manage version upgrades and schema migrations."""

    def __init__(self) -> None:
        self._migrations: List[Migration] = []

    def register(self, from_version: str, to_version: str,
                 description: str = "") -> Migration:
        mig = Migration(from_version, to_version)
        mig.description = description
        self._migrations.append(mig)
        return mig

    def apply(self, migration_id: str) -> bool:
        mig = next((m for m in self._migrations if m.migration_id == migration_id), None)
        if mig and mig.status == "pending":
            mig.status = "applied"
            mig.applied_at = time.time()
            return True
        return False

    def rollback(self, migration_id: str) -> bool:
        mig = next((m for m in self._migrations if m.migration_id == migration_id), None)
        if mig and mig.status == "applied":
            mig.status = "rolled_back"
            return True
        return False

    def get_pending(self) -> List[Migration]:
        return [m for m in self._migrations if m.status == "pending"]

    def get_applied(self) -> List[Migration]:
        return [m for m in self._migrations if m.status == "applied"]

    def get_all(self) -> List[Migration]:
        return list(self._migrations)

    def get_stats(self) -> Dict[str, Any]:
        statuses: Dict[str, int] = {}
        for m in self._migrations:
            statuses[m.status] = statuses.get(m.status, 0) + 1
        return {"total": len(self._migrations), "by_status": statuses}
