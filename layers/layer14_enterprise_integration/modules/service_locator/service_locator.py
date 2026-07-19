"""ServiceLocator — discover and access services across all layers."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional


class ServiceDescriptor:
    __slots__ = ("name", "service", "layer", "tags", "registered_at", "metadata")

    def __init__(self, name: str, service: Any, layer: str = "",
                 tags: Optional[List[str]] = None) -> None:
        self.name = name
        self.service = service
        self.layer = layer
        self.tags = tags or []
        self.registered_at = time.time()
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "layer": self.layer, "tags": self.tags}


class ServiceLocator:
    def __init__(self) -> None:
        self._services: Dict[str, ServiceDescriptor] = {}

    def register(self, name: str, service: Any, layer: str = "",
                 tags: Optional[List[str]] = None) -> ServiceDescriptor:
        desc = ServiceDescriptor(name, service, layer, tags)
        self._services[name] = desc
        return desc

    def unregister(self, name: str) -> bool:
        if name in self._services:
            del self._services[name]
            return True
        return False

    def resolve(self, name: str) -> Optional[Any]:
        desc = self._services.get(name)
        return desc.service if desc else None

    def has(self, name: str) -> bool:
        return name in self._services

    def list_services(self) -> List[Dict[str, Any]]:
        return [d.to_dict() for d in self._services.values()]

    def find_by_layer(self, layer: str) -> List[str]:
        return [d.name for d in self._services.values() if d.layer == layer]

    def find_by_tag(self, tag: str) -> List[str]:
        return [d.name for d in self._services.values() if tag in d.tags]

    def count(self) -> int:
        return len(self._services)

    def get_descriptor(self, name: str) -> Optional[ServiceDescriptor]:
        return self._services.get(name)
