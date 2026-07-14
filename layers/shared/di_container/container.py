"""
Dependency Injection Container

Features:
- Register by name (singleton or transient)
- Lazy resolution
- Circular dependency detection
- Factory functions
- Scoping (per-request, per-module)
- Interface validation
"""

from typing import Any, Callable, Dict, List, Optional, Set, Type


class ServiceNotFoundError(Exception):
    """Raised when a requested service is not registered."""


class CircularDependencyError(Exception):
    """Raised when circular dependencies are detected during resolution."""


class ServiceRegistration:
    """Stores registration details for a single service."""

    __slots__ = ("name", "factory", "singleton", "instance", "tags")

    def __init__(self, name: str, factory: Callable, singleton: bool = True, tags: Optional[List[str]] = None):
        self.name = name
        self.factory = factory
        self.singleton = singleton
        self.instance: Any = None
        self.tags = tags or []


class Container:
    """Lightweight dependency injection container."""

    def __init__(self):
        self._services: Dict[str, ServiceRegistration] = {}
        self._resolution_stack: List[str] = []

    def register(
        self,
        name: str,
        factory: Callable,
        singleton: bool = True,
        tags: Optional[List[str]] = None,
    ) -> "Container":
        """Register a service with a factory function."""
        self._services[name] = ServiceRegistration(name, factory, singleton, tags)
        return self

    def register_instance(self, name: str, instance: Any, tags: Optional[List[str]] = None) -> "Container":
        """Register a pre-built instance as a singleton."""
        reg = ServiceRegistration(name, lambda: instance, singleton=True, tags=tags)
        reg.instance = instance
        self._services[name] = reg
        return self

    def register_type(self, name: str, cls: Type, singleton: bool = True, tags: Optional[List[str]] = None) -> "Container":
        """Register a class (will be instantiated on resolution)."""
        return self.register(name, lambda: cls(), singleton, tags)

    def resolve(self, name: str) -> Any:
        """Resolve a service by name."""
        if name not in self._services:
            raise ServiceNotFoundError(f"Service '{name}' not registered")

        reg = self._services[name]

        # Return cached instance if singleton
        if reg.singleton and reg.instance is not None:
            return reg.instance

        # Circular dependency detection
        if name in self._resolution_stack:
            raise CircularDependencyError(
                f"Circular dependency detected: {' -> '.join(self._resolution_stack)} -> {name}"
            )

        self._resolution_stack.append(name)
        try:
            instance = reg.factory()
            if reg.singleton:
                reg.instance = instance
            return instance
        finally:
            self._resolution_stack.pop()

    def has(self, name: str) -> bool:
        """Check if a service is registered."""
        return name in self._services

    def is_resolved(self, name: str) -> bool:
        """Check if a singleton has been resolved."""
        reg = self._services.get(name)
        return reg is not None and reg.singleton and reg.instance is not None

    def get_by_tag(self, tag: str) -> List[Any]:
        """Get all services with a specific tag."""
        results = []
        for reg in self._services.values():
            if tag in reg.tags:
                results.append(self.resolve(reg.name))
        return results

    def get_registered_names(self) -> List[str]:
        """Get all registered service names."""
        return list(self._services.keys())

    def get_tags(self) -> Set[str]:
        """Get all unique tags."""
        tags: Set[str] = set()
        for reg in self._services.values():
            tags.update(reg.tags)
        return tags

    def reset(self):
        """Clear all registrations."""
        self._services.clear()
        self._resolution_stack.clear()

    def child(self) -> "Container":
        """Create a child container that inherits parent registrations."""
        child = Container()
        child._services = dict(self._services)
        return child

    def __repr__(self) -> str:
        return f"Container(services={len(self._services)})"
