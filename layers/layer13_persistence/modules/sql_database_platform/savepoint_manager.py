"""savepoint_manager.py — Savepoint management."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class SavePoint:
    """A transaction savepoint."""
    __slots__ = ("name", "created_at", "released", "rolled_back")
    _counter = 0

    def __init__(self, name: str = "") -> None:
        SavePoint._counter += 1
        self.name = name or f"sp_{SavePoint._counter}"
        self.created_at: float = time.time()
        self.released: bool = False
        self.rolled_back: bool = False


class SavePointManager:
    """Manages transaction savepoints."""

    def __init__(self) -> None:
        self._savepoints: Dict[str, SavePoint] = {}

    def create(self, name: str = "") -> SavePoint:
        sp = SavePoint(name)
        self._savepoints[sp.name] = sp
        return sp

    def release(self, name: str) -> bool:
        sp = self._savepoints.get(name)
        if sp and not sp.released:
            sp.released = True
            return True
        return False

    def rollback_to(self, name: str) -> bool:
        sp = self._savepoints.get(name)
        if sp and not sp.released:
            sp.rolled_back = True
            return True
        return False

    def get(self, name: str) -> Optional[SavePoint]:
        return self._savepoints.get(name)

    def list_all(self) -> List[SavePoint]:
        return list(self._savepoints.values())

    def stats(self) -> Dict[str, Any]:
        return {"total": len(self._savepoints),
                "released": sum(1 for s in self._savepoints.values() if s.released)}
