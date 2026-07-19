"""LayerRegistry — central registry for all 14 layers."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class LayerStatus(str, Enum):
    REGISTERED = "registered"
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class LayerInfo:
    __slots__ = ("layer_id", "name", "version", "status", "dependencies",
                 "services", "registered_at", "metadata")

    def __init__(self, layer_id: str, name: str, version: str = "1.0.0") -> None:
        self.layer_id = layer_id
        self.name = name
        self.version = version
        self.status = LayerStatus.REGISTERED
        self.dependencies: List[str] = []
        self.services: Dict[str, Any] = {}
        self.registered_at = time.time()
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer_id": self.layer_id, "name": self.name,
            "version": self.version, "status": self.status.value,
            "dependencies": self.dependencies,
            "services": list(self.services.keys()),
            "registered_at": self.registered_at,
        }


class LayerRegistry:
    def __init__(self) -> None:
        self._layers: Dict[str, LayerInfo] = {}
        self._service_index: Dict[str, str] = {}

    def register(self, layer_id: str, name: str, version: str = "1.0.0",
                 dependencies: Optional[List[str]] = None) -> LayerInfo:
        info = LayerInfo(layer_id, name, version)
        info.dependencies = dependencies or []
        self._layers[layer_id] = info
        return info

    def unregister(self, layer_id: str) -> bool:
        if layer_id in self._layers:
            layer = self._layers[layer_id]
            for svc in layer.services:
                self._service_index.pop(svc, None)
            del self._layers[layer_id]
            return True
        return False

    def get(self, layer_id: str) -> Optional[LayerInfo]:
        return self._layers.get(layer_id)

    def list_layers(self) -> List[Dict[str, Any]]:
        return [l.to_dict() for l in self._layers.values()]

    def register_service(self, layer_id: str, service_name: str, service: Any) -> bool:
        layer = self._layers.get(layer_id)
        if not layer:
            return False
        layer.services[service_name] = service
        self._service_index[service_name] = layer_id
        return True

    def get_service(self, service_name: str) -> Optional[Any]:
        layer_id = self._service_index.get(service_name)
        if layer_id:
            layer = self._layers.get(layer_id)
            if layer:
                return layer.services.get(service_name)
        return None

    def get_layer_for_service(self, service_name: str) -> Optional[str]:
        return self._service_index.get(service_name)

    def set_status(self, layer_id: str, status: LayerStatus) -> bool:
        layer = self._layers.get(layer_id)
        if layer:
            layer.status = status
            return True
        return False

    def get_dependencies(self, layer_id: str) -> List[str]:
        layer = self._layers.get(layer_id)
        return layer.dependencies if layer else []

    def get_dependents(self, layer_id: str) -> List[str]:
        return [lid for lid, l in self._layers.items() if layer_id in l.dependencies]

    def count(self) -> int:
        return len(self._layers)

    def summary(self) -> Dict[str, Any]:
        statuses = {}
        for l in self._layers.values():
            statuses[l.status.value] = statuses.get(l.status.value, 0) + 1
        return {"total": len(self._layers), "statuses": statuses,
                "total_services": len(self._service_index)}
