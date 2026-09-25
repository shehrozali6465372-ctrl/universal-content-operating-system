"""ServiceRegistry — dependency-safe service lifecycle registry."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class ServiceInfo:
    def __init__(self, name: str, service_type: str) -> None:
        self.service_id = f"svc_{name}"
        self.name = name
        self.service_type = service_type
        self.version = "1.0.0"
        self.status = "registered"
        self.dependencies: List[str] = []
        self.config: Dict[str, Any] = {}
        self.registered_at = time.time()
        self.last_health_check = 0.0
        self.error_count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"service_id": self.service_id, "name": self.name,
                "type": self.service_type, "version": self.version,
                "status": self.status, "dependencies": list(self.dependencies)}


class ServiceRegistry:
    def __init__(self) -> None:
        self._services: Dict[str, ServiceInfo] = {}

    def register(self, name: str, service_type: str = "", version: str = "1.0.0",
                 dependencies: Optional[List[str]] = None,
                 config: Optional[Dict[str, Any]] = None) -> ServiceInfo:
        if not name:
            raise ValueError("name is required")
        if name in self._services:
            return self._services[name]
        service = ServiceInfo(name, service_type)
        service.version = version
        service.dependencies = list(dependencies or [])
        service.config = dict(config or {})
        self._services[name] = service
        return service

    def unregister(self, name: str) -> bool:
        return self._services.pop(name, None) is not None

    def get(self, name: str) -> Optional[ServiceInfo]:
        return self._services.get(name)

    def start(self, name: str) -> bool:
        service = self._services.get(name)
        if service is None:
            return False
        if any(self._services.get(dep) is None or self._services[dep].status != "running"
               for dep in service.dependencies):
            return False
        service.status = "running"
        return True

    def stop(self, name: str) -> bool:
        service = self._services.get(name)
        if service is None:
            return False
        service.status = "stopped"
        return True

    def get_all(self) -> List[ServiceInfo]:
        return list(self._services.values())

    def get_by_type(self, service_type: str) -> List[ServiceInfo]:
        return [service for service in self._services.values()
                if service.service_type == service_type]

    def get_running(self) -> List[ServiceInfo]:
        return [service for service in self._services.values() if service.status == "running"]

    def check_health(self, name: str) -> bool:
        service = self._services.get(name)
        if service is None:
            return False
        service.last_health_check = time.time()
        return service.status == "running"

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        statuses: Dict[str, int] = {}
        for service in self._services.values():
            types[service.service_type] = types.get(service.service_type, 0) + 1
            statuses[service.status] = statuses.get(service.status, 0) + 1
        return {"total": len(self._services), "by_type": types, "by_status": statuses}
