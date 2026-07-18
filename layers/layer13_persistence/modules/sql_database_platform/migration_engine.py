"""migration_engine.py — Database migration engine."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class Migration:
    """Single migration."""
    __slots__ = ("migration_id", "version", "name", "up_sql", "down_sql",
                 "applied_at", "status")
    _counter = 0

    def __init__(self, version: str, name: str, up_sql: str, down_sql: str = "") -> None:
        Migration._counter += 1
        self.migration_id: int = Migration._counter
        self.version = version
        self.name = name
        self.up_sql = up_sql
        self.down_sql = down_sql
        self.applied_at: float = 0.0
        self.status: str = "pending"

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.migration_id, "version": self.version, "name": self.name,
                "status": self.status}


class MigrationEngine:
    """Manages database migrations."""

    def __init__(self) -> None:
        self._migrations: Dict[str, Migration] = {}
        self._applied: List[Migration] = []
        self._current_version: str = "0.0.0"

    def add_migration(self, migration: Migration) -> None:
        self._migrations[migration.version] = migration

    def migrate_up(self, target_version: str = "") -> List[Migration]:
        applied = []
        for ver in sorted(self._migrations.keys()):
            if ver <= target_version or (not target_version and ver > self._current_version):
                m = self._migrations[ver]
                m.status = "applied"
                m.applied_at = time.time()
                self._applied.append(m)
                self._current_version = ver
                applied.append(m)
        return applied

    def migrate_down(self, target_version: str) -> List[Migration]:
        rolled_back = []
        for m in reversed(self._applied):
            if m.version > target_version:
                m.status = "rolled_back"
                rolled_back.append(m)
                self._applied.remove(m)
        if rolled_back:
            self._current_version = target_version
        return rolled_back

    def get_current_version(self) -> str:
        return self._current_version

    def get_pending(self) -> List[Migration]:
        return [m for m in self._migrations.values() if m.status == "pending"]

    def get_applied(self) -> List[Migration]:
        return list(self._applied)

    def stats(self) -> Dict[str, Any]:
        return {"total": len(self._migrations), "applied": len(self._applied),
                "pending": len(self.get_pending()), "current_version": self._current_version}
