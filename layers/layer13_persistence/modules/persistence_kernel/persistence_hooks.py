"""persistence_hooks.py — Lifecycle hooks."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List


class PersistenceHooks:
    """Lifecycle hooks for persistence events."""

    def __init__(self) -> None:
        self._hooks: Dict[str, List[Callable]] = {}
        self._history: List[Dict[str, Any]] = []

    def register(self, event: str, handler: Callable) -> None:
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(handler)

    def unregister(self, event: str, handler: Callable) -> bool:
        if event in self._hooks:
            self._hooks[event] = [h for h in self._hooks[event] if h != handler]
            return True
        return False

    def fire(self, event: str, data: Dict[str, Any] = None) -> int:
        count = 0
        for handler in self._hooks.get(event, []):
            try:
                handler(data or {})
                count += 1
            except Exception:
                pass
        self._history.append({"event": event, "handlers_called": count,
                               "time": time.time()})
        return count

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._history[-limit:]

    def list_events(self) -> List[str]:
        return list(self._hooks.keys())

    def stats(self) -> Dict[str, Any]:
        total_handlers = sum(len(h) for h in self._hooks.values())
        return {"events": len(self._hooks), "total_handlers": total_handlers,
                "fired": len(self._history)}
