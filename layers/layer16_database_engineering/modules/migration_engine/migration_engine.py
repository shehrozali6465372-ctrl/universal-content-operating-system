"""MigrationEngine — schema migration and versioning."""
from __future__ import annotations
import time
import uuid
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class MigrationStatus(str, Enum):
    PENDING = "pending"; RUNNING = "running"; APPLIED = "applied"
    FAILED = "failed"; ROLLED_BACK = "rolled_back"


class Migration:
    __slots__ = ("migration_id", "version", "name", "up_fn", "down_fn",
                 "status", "applied_at", "duration_ms", "metadata")

    def __init__(self, version: str, name: str, up_fn: Callable,
                 down_fn: Optional[Callable] = None) -> None:
        self.migration_id = str(uuid.uuid4())[:12]
        self.version = version
        self.name = name
        self.up_fn = up_fn
        self.down_fn = down_fn
        self.status = MigrationStatus.PENDING
        self.applied_at: float = 0.0
        self.duration_ms: float = 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"migration_id": self.migration_id, "version": self.version,
                "name": self.name, "status": self.status.value}


class MigrationEngine:
    def __init__(self) -> None:
        self._migrations: List[Migration] = []
        self._applied: Dict[str, Migration] = {}
        self._history: List[Dict[str, Any]] = []

    def add_migration(self, version: str, name: str, up_fn: Callable,
                      down_fn: Optional[Callable] = None) -> Migration:
        m = Migration(version, name, up_fn, down_fn)
        self._migrations.append(m)
        self._migrations.sort(key=lambda x: x.version)
        return m

    def migrate_up(self, target_version: Optional[str] = None) -> Dict[str, Any]:
        applied = []
        for m in self._migrations:
            if m.status == MigrationStatus.APPLIED:
                continue
            if target_version and m.version > target_version:
                break
            m.status = MigrationStatus.RUNNING
            start = time.time()
            try:
                m.up_fn()
                m.status = MigrationStatus.APPLIED
                m.applied_at = time.time()
                m.duration_ms = (time.time() - start) * 1000
                self._applied[m.version] = m
                applied.append(m.to_dict())
            except Exception as exc:
                m.status = MigrationStatus.FAILED
                self._history.append({"version": m.version, "error": str(exc)})
                return {"applied": applied, "failed": m.to_dict(), "error": str(exc)}
        return {"applied": applied, "total": len(applied)}

    def migrate_down(self, version: str) -> Dict[str, Any]:
        rolled_back = []
        for m in reversed(self._migrations):
            if m.version < version:
                break
            if m.status != MigrationStatus.APPLIED:
                continue
            if not m.down_fn:
                return {"error": f"No down migration for {m.version}"}
            try:
                m.down_fn()
                m.status = MigrationStatus.ROLLED_BACK
                del self._applied[m.version]
                rolled_back.append(m.to_dict())
            except Exception as exc:
                return {"error": str(exc), "rolled_back": rolled_back}
        return {"rolled_back": rolled_back}

    def current_version(self) -> Optional[str]:
        if self._applied:
            return max(self._applied.keys())
        return None

    def pending(self) -> List[Dict[str, Any]]:
        return [m.to_dict() for m in self._migrations if m.status == MigrationStatus.PENDING]

    def applied(self) -> List[Dict[str, Any]]:
        return [m.to_dict() for m in self._migrations if m.status == MigrationStatus.APPLIED]

    def list_migrations(self) -> List[Dict[str, Any]]:
        return [m.to_dict() for m in self._migrations]
