"""ServiceRegistry — Track all services, dependencies, versions, and health."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class ServiceInfo:
    """Information about a registered service."""

    __slots__ = ("service_id", "name", "service_type", "version",
                 "status", "dependencies", "config", "registered_at",
                 "last_health_check", "error_count")

    def __init__(self, name: str = "", service_type: str = "") -> None:
        self.service_id: str = f"svc_{name}"
        self.name = name
        self.service_type = service_type
        self.version: str = "1.0.0"
        self.status: str = "registered"
        self.dependencies: List[str] = []
        self.config: Dict[str, Any] = {}
        self.registered_at: float = time.time()
        self.last_health_check: float = 0.0
        self.error_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"service_id": self.service_id, "name": self.name,
                "type": self.service_type, "version": self.version,
                "status": self.status, "dependencies": self.dependencies}


class ServiceRegistry:
    """Central registry for all services with dependency tracking."""

    def __init__(self) -> None:
        self._services: Dict[str, ServiceInfo] = {}

    def register(self, name: str, service_type: str = "",
                 version: str = "1.0.0",
                 dependencies: Optional[List[str]] = None,
                 config: Optional[Dict[str, Any]] = None) -> ServiceInfo:
        if name in self._services:
            return self._services[name]
        svc = ServiceInfo(name, service_type)
        svc.version = version
        if dependencies:
            svc.dependencies = list(dependencies)
        if config:
            svc.config = dict(config)
        self._services[name] = svc
        return svc

    def unregister(self, name: str) -> bool:
        return self._services.pop(name, None) is not None

    def get(self, name: str) -> Optional[ServiceInfo]:
        return self._services.get(name)

    def start(self, name: str) -> bool:
        svc = self._services.get(name)
        if svc is None:
            return False
        for dep in svc.dependencies:
            dep_svc = self._services.get(dep)
            if dep_svc and dep_svc.status != "running":
                return False
        svc.status = "running"
        return True

    def stop(self, name: str) -> bool:
        svc = self._services.get(name)
        if svc:
            svc.status = "stopped"
            return True
        return False

    def get_all(self) -> List[ServiceInfo]:
        return list(self._services.values())

    def get_by_type(self, service_type: str) -> List[ServiceInfo]:
        return [s for s in self._services.values() if s.service_type == service_type]

    def get_running(self) -> List[ServiceInfo]:
        return [s for s in self._services.values() if s.status == "running"]

    def check_health(self, name: str) -> bool:
        svc = self._services.get(name)
        if svc:
            svc.last_health_check = time.time()
            return svc.status == "running"
        return False

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        statuses: Dict[str, int] = {}
        for s in self._services.values():
            types[s.service_type] = types.get(s.service_type, 0) + 1
            statuses[s.status] = statuses.get(s.status, 0) + 1
        return {"total": len(self._services), "by_type": types, "by_status": statuses}
