"""
Dependency Injection Container
Loose coupling between layers via interface-based DI.

Usage:
    from layers.shared.di_container import Container

    container = Container()
    container.register("logger", lambda: Logger())
    container.register("db", lambda: DatabaseManager(config))

    logger = container.resolve("logger")
"""
from layers.shared.di_container.container import Container, ServiceNotFoundError, CircularDependencyError

__all__ = ["Container", "ServiceNotFoundError", "CircularDependencyError"]
