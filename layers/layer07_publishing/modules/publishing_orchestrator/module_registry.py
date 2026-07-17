"""Module Registry — Register and discover Layer 7 modules."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class ModuleInfo:
    """Information about a registered module."""

    __slots__ = ("name", "version", "description", "enabled", "status")

    def __init__(self, name: str = "", version: str = "1.0.0") -> None:
        self.name = name
        self.version = version
        self.description: str = ""
        self.enabled: bool = True
        self.status: str = "ready"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "enabled": self.enabled,
            "status": self.status,
        }


class ModuleRegistry:
    """Registry for Layer 7 publishing modules."""

    def __init__(self) -> None:
        self._modules: Dict[str, ModuleInfo] = {}
        self._initialize_defaults()

    def _initialize_defaults(self) -> None:
        defaults = [
            ("publishing_planner", "1.0.0"),
            ("platform_plugin_manager", "1.0.0"),
            ("media_manager", "1.0.0"),
            ("scheduler_queue", "1.0.0"),
            ("publisher_engine", "1.0.0"),
            ("failure_recovery", "1.0.0"),
            ("analytics_hook", "1.0.0"),
            ("publishing_memory", "1.0.0"),
            ("publishing_policies", "1.0.0"),
            ("publishing_orchestrator", "1.0.0"),
        ]
        for name, version in defaults:
            self._modules[name] = ModuleInfo(name, version)

    def register(self, name: str, version: str = "1.0.0", description: str = "") -> ModuleInfo:
        info = ModuleInfo(name, version)
        info.description = description
        self._modules[name] = info
        return info

    def get_module(self, name: str) -> Optional[ModuleInfo]:
        return self._modules.get(name)

    def get_all_modules(self) -> List[ModuleInfo]:
        return list(self._modules.values())

    def get_enabled_modules(self) -> List[ModuleInfo]:
        return [m for m in self._modules.values() if m.enabled]

    def disable_module(self, name: str) -> bool:
        if name in self._modules:
            self._modules[name].enabled = False
            return True
        return False

    def enable_module(self, name: str) -> bool:
        if name in self._modules:
            self._modules[name].enabled = True
            return True
        return False

    @property
    def module_count(self) -> int:
        return len(self._modules)

    @property
    def enabled_count(self) -> int:
        return sum(1 for m in self._modules.values() if m.enabled)
