"""DIContainer — dependency injection container for all layers."""
from __future__ import annotations
from typing import Any, Dict, Optional, TypeVar, Callable

T = TypeVar('T')

class DIContainer:
    _instance: Optional['DIContainer'] = None

    def __new__(cls) -> 'DIContainer':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._services: Dict[str, Any] = {}
            cls._instance._factories: Dict[str, Callable] = {}
            cls._instance._singletons: Dict[str, Any] = {}
        return cls._instance

    def register(self, name: str, instance: Any) -> None:
        self._services[name] = instance

    def register_factory(self, name: str, factory: Callable) -> None:
        self._factories[name] = factory

    def register_singleton(self, name: str, instance: Any) -> None:
        self._singletons[name] = instance

    def get(self, name: str, default: Any = None) -> Any:
        if name in self._singletons:
            return self._singletons[name]
        if name in self._services:
            return self._services[name]
        if name in self._factories:
            instance = self._factories[name]()
            self._singletons[name] = instance
            return instance
        return default

    def has(self, name: str) -> bool:
        return name in self._singletons or name in self._services or name in self._factories

    def list_services(self) -> Dict[str, str]:
        all_s = {}
        for k in self._singletons: all_s[k] = 'singleton'
        for k in self._services: all_s[k] = 'instance'
        for k in self._factories: all_s[k] = 'factory'
        return all_s

    def clear(self) -> None:
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
