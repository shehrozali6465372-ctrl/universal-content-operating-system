"""event_versioning.py — Event schema versioning."""
from __future__ import annotations
from typing import Any, Dict, List


class EventVersion:
    """Event schema version."""
    __slots__ = ("event_type", "version", "schema", "migrated_from")

    def __init__(self, event_type: str, version: int, schema: Dict[str, Any] = None) -> None:
        self.event_type = event_type
        self.version = version
        self.schema = schema or {}
        self.migrated_from: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.event_type, "version": self.version}


class EventVersionManager:
    """Manages event schema versions."""

    def __init__(self) -> None:
        self._versions: Dict[str, List[EventVersion]] = {}

    def register(self, event_type: str, version: int,
                 schema: Dict[str, Any] = None) -> EventVersion:
        if event_type not in self._versions:
            self._versions[event_type] = []
        ev = EventVersion(event_type, version, schema)
        self._versions[event_type].append(ev)
        return ev

    def get_latest(self, event_type: str) -> EventVersion:
        versions = self._versions.get(event_type, [])
        return versions[-1] if versions else None

    def get_all(self, event_type: str) -> List[EventVersion]:
        return list(self._versions.get(event_type, []))

    def stats(self) -> Dict[str, Any]:
        total = sum(len(v) for v in self._versions.values())
        return {"types": len(self._versions), "total_versions": total}
