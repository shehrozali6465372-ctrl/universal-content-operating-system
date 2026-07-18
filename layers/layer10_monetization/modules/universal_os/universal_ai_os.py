"""UniversalAIOS — Main OS kernel for the entire system."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class SystemState:
    """Current system state."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    RECOVERING = "recovering"


class UniversalAIOS:
    """Main OS kernel — start, stop, pause, resume, restart, health."""

    def __init__(self) -> None:
        self._state = SystemState.STOPPED
        self._started_at: Optional[float] = None
        self._stopped_at: Optional[float] = None
        self._paused_at: Optional[float] = None
        self._components: Dict[str, Any] = {}
        self._services: Dict[str, Any] = {}
        self._events: List[Dict[str, Any]] = []
        self._error_count: int = 0
        self._recovery_count: int = 0

    def start(self) -> bool:
        if self._state == SystemState.RUNNING:
            return True
        self._state = SystemState.STARTING
        self._record_event("system_starting")
        self._state = SystemState.RUNNING
        self._started_at = time.time()
        self._record_event("system_started")
        return True

    def stop(self) -> bool:
        if self._state == SystemState.STOPPED:
            return True
        self._state = SystemState.STOPPING
        self._record_event("system_stopping")
        self._state = SystemState.STOPPED
        self._stopped_at = time.time()
        self._record_event("system_stopped")
        return True

    def pause(self) -> bool:
        if self._state != SystemState.RUNNING:
            return False
        self._state = SystemState.PAUSED
        self._paused_at = time.time()
        self._record_event("system_paused")
        return True

    def resume(self) -> bool:
        if self._state != SystemState.PAUSED:
            return False
        self._state = SystemState.RUNNING
        self._record_event("system_resumed")
        return True

    def restart(self) -> bool:
        self.stop()
        self.start()
        self._record_event("system_restarted")
        return True

    def shutdown(self) -> bool:
        return self.stop()

    def status(self) -> Dict[str, Any]:
        uptime = 0.0
        if self._started_at and self._state == SystemState.RUNNING:
            uptime = time.time() - self._started_at
        return {"state": self._state, "uptime_seconds": round(uptime, 1),
                "components": len(self._components),
                "services": len(self._services),
                "total_events": len(self._events),
                "error_count": self._error_count,
                "recovery_count": self._recovery_count}

    def health(self) -> Dict[str, Any]:
        unhealthy = []
        for name, svc in self._services.items():
            if hasattr(svc, "is_healthy") and not svc.is_healthy():
                unhealthy.append(name)
        return {"healthy": self._state == SystemState.RUNNING and len(unhealthy) == 0,
                "state": self._state, "unhealthy_services": unhealthy}

    def register_component(self, name: str, component: Any) -> None:
        self._components[name] = component

    def register_service(self, name: str, service: Any) -> None:
        self._services[name] = service

    def get_component(self, name: str) -> Any:
        return self._components.get(name)

    def get_service(self, name: str) -> Any:
        return self._services.get(name)

    def _record_event(self, event_type: str) -> None:
        self._events.append({"type": event_type, "timestamp": time.time()})
