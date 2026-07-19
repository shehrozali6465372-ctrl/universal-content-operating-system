"""GovernanceEvents — event system for governance operations."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List

class GovernanceEvents:
    def __init__(self) -> None:
        self._subs: Dict[str, List[Callable]] = {}; self._log: List[Dict[str, Any]] = []
    def subscribe(self, etype: str, cb: Callable) -> None: self._subs.setdefault(etype, []).append(cb)
    def publish(self, etype: str, data: Dict[str, Any] | None = None) -> None:
        entry = {"event": etype, "data": data or {}, "time": time.time()}; self._log.append(entry)
        for cb in self._subs.get(etype, []):
            try: cb(data or {})
            except Exception: pass
    def get_log(self, etype: str | None = None) -> List[Dict[str, Any]]:
        if etype: return [e for e in self._log if e["event"] == etype]
        return list(self._log)
    def clear(self) -> None: self._log.clear()
