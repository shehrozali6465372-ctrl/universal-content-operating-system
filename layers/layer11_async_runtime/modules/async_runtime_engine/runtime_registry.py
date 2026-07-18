"""RuntimeRegistry — Register and discover runtime components."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class RuntimeComponent:
    """A registered runtime component."""
    __slots__ = ("name", "component_type", "version", "status", "config", "registered_at")

    def __init__(self, name: str = "", component_type: str = "") -> None:
        self.name = name
        self.component_type = component_type
        self.version: str = "1.0.0"
        self.status: str = "registered"
        self.config: Dict[str, Any] = {}
        self.registered_at: float = time.time()


class RuntimeRegistry:
    """Registry for runtime components."""

    def __init__(self) -> None:
        self._components: Dict[str, RuntimeComponent] = {}

    def register(self, name: str, component_type: str = "",
                 version: str = "1.0.0") -> RuntimeComponent:
        if name in self._components:
            return self._components[name]
        comp = RuntimeComponent(name, component_type)
        comp.version = version
        self._components[name] = comp
        return comp

    def unregister(self, name: str) -> bool:
        return self._components.pop(name, None) is not None

    def get(self, name: str) -> Optional[RuntimeComponent]:
        return self._components.get(name)

    def get_by_type(self, component_type: str) -> List[RuntimeComponent]:
        return [c for c in self._components.values() if c.component_type == component_type]

    def get_all(self) -> List[RuntimeComponent]:
        return list(self._components.values())

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for c in self._components.values():
            types[c.component_type] = types.get(c.component_type, 0) + 1
        return {"total": len(self._components), "by_type": types}
