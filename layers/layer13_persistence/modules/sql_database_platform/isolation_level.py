"""isolation_level.py — Transaction isolation levels."""
from __future__ import annotations
from enum import IntEnum
from typing import Any, Dict


class IsolationLevel(IntEnum):
    READ_UNCOMMITTED = 0
    READ_COMMITTED = 1
    REPEATABLE_READ = 2
    SERIALIZABLE = 3


ISOLATION_NAMES = {
    IsolationLevel.READ_UNCOMMITTED: "READ UNCOMMITTED",
    IsolationLevel.READ_COMMITTED: "READ COMMITTED",
    IsolationLevel.REPEATABLE_READ: "REPEATABLE READ",
    IsolationLevel.SERIALIZABLE: "SERIALIZABLE",
}


class IsolationManager:
    """Manages transaction isolation levels."""

    def __init__(self) -> None:
        self._current: IsolationLevel = IsolationLevel.READ_COMMITTED
        self._history: list = []

    def set_level(self, level: IsolationLevel) -> None:
        self._current = level
        self._history.append({"level": ISOLATION_NAMES[level]})

    def get_level(self) -> IsolationLevel:
        return self._current

    def get_level_name(self) -> str:
        return ISOLATION_NAMES.get(self._current, "UNKNOWN")

    def to_dict(self) -> Dict[str, Any]:
        return {"level": self.get_level_name(), "history": len(self._history)}
