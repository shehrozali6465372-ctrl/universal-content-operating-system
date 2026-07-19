"""LifecycleManager — manage startup/shutdown lifecycle of all components."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class ComponentState(str, Enum):
    CREATED = "created"; STARTING = "starting"; RUNNING = "running"
    STOPPING = "stopping"; STOPPED = "stopped"; ERROR = "error"


class LifecycleComponent:
    __slots__ = ("name", "state", "start_fn", "stop_fn", "health_fn",
                 "started_at", "stopped_at", "error", "metadata")

    def __init__(self, name: str, start_fn: Optional[Callable] = None,
                 stop_fn: Optional[Callable] = None,
                 health_fn: Optional[Callable] = None) -> None:
        self.name = name
        self.state = ComponentState.CREATED
        self.start_fn = start_fn
        self.stop_fn = stop_fn
        self.health_fn = health_fn
        self.started_at: float = 0.0
        self.stopped_at: float = 0.0
        self.error: Optional[str] = None
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "state": self.state.value,
                "error": self.error}


class LifecycleManager:
    def __init__(self) -> None:
        self._components: Dict[str, LifecycleComponent] = {}
        self._order: List[str] = []
        self._history: List[Dict[str, Any]] = []

    def register(self, name: str, start_fn: Optional[Callable] = None,
                 stop_fn: Optional[Callable] = None,
                 health_fn: Optional[Callable] = None) -> LifecycleComponent:
        comp = LifecycleComponent(name, start_fn, stop_fn, health_fn)
        self._components[name] = comp
        self._order.append(name)
        return comp

    def unregister(self, name: str) -> bool:
        if name in self._components:
            del self._components[name]
            self._order = [n for n in self._order if n != name]
            return True
        return False

    def start_component(self, name: str) -> Dict[str, Any]:
        comp = self._components.get(name)
        if not comp:
            return {"error": "not_found"}
        comp.state = ComponentState.STARTING
        try:
            if comp.start_fn:
                comp.start_fn()
            comp.state = ComponentState.RUNNING
            comp.started_at = time.time()
        except Exception as exc:
            comp.state = ComponentState.ERROR
            comp.error = str(exc)
            return {"error": str(exc)}
        self._history.append({"action": "start", **comp.to_dict(), "time": time.time()})
        return {"status": "started", "component": name}

    def stop_component(self, name: str) -> Dict[str, Any]:
        comp = self._components.get(name)
        if not comp:
            return {"error": "not_found"}
        comp.state = ComponentState.STOPPING
        try:
            if comp.stop_fn:
                comp.stop_fn()
            comp.state = ComponentState.STOPPED
            comp.stopped_at = time.time()
        except Exception as exc:
            comp.state = ComponentState.ERROR
            comp.error = str(exc)
            return {"error": str(exc)}
        self._history.append({"action": "stop", **comp.to_dict(), "time": time.time()})
        return {"status": "stopped", "component": name}

    def start_all(self) -> Dict[str, Any]:
        results = []
        for name in self._order:
            results.append(self.start_component(name))
        failed = [r for r in results if "error" in r]
        return {"started": len(results) - len(failed), "failed": len(failed), "results": results}

    def stop_all(self) -> Dict[str, Any]:
        results = []
        for name in reversed(self._order):
            results.append(self.stop_component(name))
        failed = [r for r in results if "error" in r]
        return {"stopped": len(results) - len(failed), "failed": len(failed)}

    def health_check(self, name: str) -> Dict[str, Any]:
        comp = self._components.get(name)
        if not comp:
            return {"name": name, "status": "not_found"}
        if comp.health_fn:
            try:
                return {"name": name, "status": comp.state.value, "health": comp.health_fn()}
            except Exception as exc:
                return {"name": name, "status": "error", "error": str(exc)}
        return {"name": name, "status": comp.state.value}

    def status(self) -> Dict[str, Any]:
        states = {}
        for comp in self._components.values():
            states[comp.state.value] = states.get(comp.state.value, 0) + 1
        return {"total": len(self._components), "states": states, "order": self._order}

    def get_component(self, name: str) -> Optional[LifecycleComponent]:
        return self._components.get(name)

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
