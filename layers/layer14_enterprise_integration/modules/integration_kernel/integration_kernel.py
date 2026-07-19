"""IntegrationKernel — central nervous system of the AI OS."""
from __future__ import annotations
import time
import threading
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class KernelState(str, Enum):
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class IntegrationKernel:
    """Central kernel that coordinates all integration subsystems."""

    def __init__(self) -> None:
        self._state = KernelState.INITIALIZED
        self._subsystems: Dict[str, Any] = {}
        self._hooks: Dict[str, List[Callable]] = {
            "before_start": [], "after_start": [],
            "before_stop": [], "after_stop": [],
            "on_error": [],
        }
        self._start_time: float = 0.0
        self._lock = threading.Lock()
        self._errors: List[Dict[str, Any]] = []

    @property
    def state(self) -> KernelState:
        return self._state

    @property
    def uptime(self) -> float:
        if self._state == KernelState.RUNNING:
            return round(time.time() - self._start_time, 3)
        return 0.0

    def register_subsystem(self, name: str, subsystem: Any) -> None:
        with self._lock:
            self._subsystems[name] = subsystem

    def get_subsystem(self, name: str) -> Optional[Any]:
        return self._subsystems.get(name)

    def list_subsystems(self) -> List[str]:
        return list(self._subsystems.keys())

    def add_hook(self, event: str, callback: Callable) -> None:
        if event in self._hooks:
            self._hooks[event].append(callback)

    def _fire_hooks(self, event: str) -> None:
        for cb in self._hooks.get(event, []):
            try:
                cb()
            except Exception as exc:
                self._errors.append({"hook": event, "error": str(exc), "time": time.time()})

    def start(self) -> Dict[str, Any]:
        with self._lock:
            if self._state == KernelState.RUNNING:
                return {"status": "already_running"}
            self._state = KernelState.STARTING
        self._fire_hooks("before_start")
        self._start_time = time.time()
        with self._lock:
            self._state = KernelState.RUNNING
        self._fire_hooks("after_start")
        return {"status": "started", "subsystems": len(self._subsystems)}

    def stop(self) -> Dict[str, Any]:
        with self._lock:
            if self._state != KernelState.RUNNING:
                return {"status": "not_running"}
            self._state = KernelState.STOPPING
        self._fire_hooks("before_stop")
        with self._lock:
            self._state = KernelState.STOPPED
        self._fire_hooks("after_stop")
        return {"status": "stopped", "uptime": self.uptime}

    def status(self) -> Dict[str, Any]:
        return {
            "state": self._state.value,
            "uptime": self.uptime,
            "subsystems": self.list_subsystems(),
            "subsystem_count": len(self._subsystems),
            "errors": len(self._errors),
            "hooks": {k: len(v) for k, v in self._hooks.items()},
        }

    def get_errors(self) -> List[Dict[str, Any]]:
        return list(self._errors)

    def clear_errors(self) -> None:
        self._errors.clear()
