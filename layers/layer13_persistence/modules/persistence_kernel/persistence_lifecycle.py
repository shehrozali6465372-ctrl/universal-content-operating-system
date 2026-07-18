"""persistence_lifecycle.py — Persistence lifecycle management."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List


class LifecycleEvent:
    """Single lifecycle event."""
    __slots__ = ("event_type", "store_name", "data", "timestamp", "success")

    def __init__(self, event_type: str, store_name: str, data: Dict[str, Any] = None,
                 success: bool = True) -> None:
        self.event_type = event_type
        self.store_name = store_name
        self.data = data or {}
        self.timestamp = time.time()
        self.success = success

    def to_dict(self) -> Dict[str, Any]:
        return {"event_type": self.event_type, "store_name": self.store_name,
                "timestamp": self.timestamp, "success": self.success}


class PersistenceLifecycle:
    """Manages the lifecycle of persistence stores."""

    __slots__ = ("_stores", "_hooks", "_events", "_states")

    def __init__(self) -> None:
        self._stores: Dict[str, Any] = {}
        self._hooks: Dict[str, List[Callable]] = {}
        self._events: List[LifecycleEvent] = []
        self._states: Dict[str, str] = {}

    def register(self, name: str, store: Any) -> None:
        self._stores[name] = store
        self._states[name] = "registered"

    def on(self, event_type: str, handler: Callable) -> None:
        if event_type not in self._hooks:
            self._hooks[event_type] = []
        self._hooks[event_type].append(handler)

    def initialize_store(self, name: str) -> bool:
        store = self._stores.get(name)
        if store and hasattr(store, "initialize"):
            try:
                store.initialize()
                self._states[name] = "initialized"
                self._fire_event(LifecycleEvent("initialized", name))
                return True
            except Exception:
                self._states[name] = "error"
                self._fire_event(LifecycleEvent("init_failed", name, success=False))
                return False
        self._states[name] = "initialized"
        self._fire_event(LifecycleEvent("initialized", name))
        return True

    def close_store(self, name: str) -> bool:
        store = self._stores.get(name)
        if store and hasattr(store, "close"):
            try:
                store.close()
            except Exception:
                pass
        self._states[name] = "closed"
        self._fire_event(LifecycleEvent("closed", name))
        return True

    def get_state(self, name: str) -> str:
        return self._states.get(name, "unknown")

    def get_all_states(self) -> Dict[str, str]:
        return dict(self._states)

    def get_events(self, name: str = "", limit: int = 50) -> List[LifecycleEvent]:
        events = self._events
        if name:
            events = [e for e in events if e.store_name == name]
        return events[-limit:]

    def _fire_event(self, event: LifecycleEvent) -> None:
        self._events.append(event)
        for handler in self._hooks.get(event.event_type, []):
            try:
                handler(event)
            except Exception:
                pass

    def to_dict(self) -> Dict[str, Any]:
        return {"stores": len(self._stores), "states": dict(self._states),
                "events": len(self._events)}
