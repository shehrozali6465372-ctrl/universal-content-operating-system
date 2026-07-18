"""event_recovery.py — Event recovery."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.event_store.event import Event


class EventRecovery:
    """Recovers from event store failures."""

    def __init__(self) -> None:
        self._recovery_log: List[Dict[str, Any]] = []
        self._recovered_count: int = 0

    def recover_from_store(self, events: List[Event], from_version: int = 0) -> List[Event]:
        recovered = [e for e in events if e.version >= from_version]
        self._recovered_count += len(recovered)
        self._recovery_log.append({"from_version": from_version, "recovered": len(recovered)})
        return recovered

    def get_recovery_log(self) -> List[Dict[str, Any]]:
        return list(self._recovery_log)

    def stats(self) -> Dict[str, Any]:
        return {"recoveries": len(self._recovery_log), "total_recovered": self._recovered_count}
