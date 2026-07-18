"""SystemKernel — Low-level kernel managing components, services, and execution."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional


class Service:
    """A registered system service."""

    __slots__ = ("name", "service_type", "status", "dependencies",
                 "version", "health_check", "registered_at")

    def __init__(self, name: str = "", service_type: str = "") -> None:
        self.name = name
        self.service_type = service_type
        self.status: str = "registered"
        self.dependencies: List[str] = []
        self.version: str = "1.0.0"
        self.health_check: Optional[Callable] = None
        self.registered_at: float = time.time()

    def is_healthy(self) -> bool:
        if self.health_check:
            return self.health_check()
        return self.status == "running"

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "type": self.service_type,
                "status": self.status, "version": self.version,
                "dependencies": self.dependencies}


class SystemKernel:
    """Low-level kernel — manage services, execution, and component lifecycle."""

    def __init__(self) -> None:
        self._services: Dict[str, Service] = {}
        self._execution_log: List[Dict[str, Any]] = []

    def register_service(self, name: str, service_type: str,
                         dependencies: Optional[List[str]] = None,
                         version: str = "1.0.0") -> Service:
        if name in self._services:
            return self._services[name]
        svc = Service(name, service_type)
        if dependencies:
            svc.dependencies = list(dependencies)
        svc.version = version
        self._services[name] = svc
        return svc

    def start_service(self, name: str) -> bool:
        svc = self._services.get(name)
        if svc is None:
            return False
        for dep in svc.dependencies:
            dep_svc = self._services.get(dep)
            if dep_svc and dep_svc.status != "running":
                return False
        svc.status = "running"
        self._log(name, "started")
        return True

    def stop_service(self, name: str) -> bool:
        svc = self._services.get(name)
        if svc is None:
            return False
        svc.status = "stopped"
        self._log(name, "stopped")
        return True

    def get_service(self, name: str) -> Optional[Service]:
        return self._services.get(name)

    def get_all_services(self) -> List[Service]:
        return list(self._services.values())

    def get_running_services(self) -> List[Service]:
        return [s for s in self._services.values() if s.status == "running"]

    def check_dependencies(self, name: str) -> bool:
        svc = self._services.get(name)
        if svc is None:
            return False
        return all(
            self._services.get(d) is not None and self._services[d].status == "running"
            for d in svc.dependencies
        )

    def get_execution_log(self, count: int = 10) -> List[Dict[str, Any]]:
        return self._execution_log[-count:]

    def _log(self, service_name: str, action: str) -> None:
        self._execution_log.append({"service": service_name,
                                     "action": action, "timestamp": time.time()})

    def get_stats(self) -> Dict[str, Any]:
        statuses: Dict[str, int] = {}
        for s in self._services.values():
            statuses[s.status] = statuses.get(s.status, 0) + 1
        return {"total": len(self._services), "by_status": statuses}
