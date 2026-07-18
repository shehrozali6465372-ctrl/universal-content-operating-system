"""event_archive.py — Event archival."""
from __future__ import annotations
import time
from typing import Any, Dict, List
from layers.layer13_persistence.modules.event_store.event import Event


class EventArchive:
    """Archives old events."""

    def __init__(self, max_age_days: int = 90) -> None:
        self._max_age_seconds = max_age_days * 86400
        self._archived: List[Event] = []
        self._archive_count: int = 0

    def archive(self, events: List[Event]) -> List[Event]:
        now = time.time()
        to_archive = [e for e in events if (now - e.timestamp) > self._max_age_seconds]
        self._archived.extend(to_archive)
        self._archive_count += len(to_archive)
        return to_archive

    def get_archived(self, limit: int = 100) -> List[Event]:
        return self._archived[-limit:]

    def archived_count(self) -> int:
        return len(self._archived)

    def stats(self) -> Dict[str, Any]:
        return {"archived": self.archived_count(), "max_age_days": self._max_age_seconds // 86400}
