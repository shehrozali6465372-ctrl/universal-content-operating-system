"""persistence_configuration.py — Persistence configuration."""
from __future__ import annotations
from typing import Any, Dict


class PersistenceConfiguration:
    """Configuration for the persistence system."""

    __slots__ = ("database_url", "redis_url", "vector_db_url", "object_storage_url",
                 "enable_cache", "enable_vector", "enable_backup", "enable_replication",
                 "pool_size", "max_overflow", "pool_timeout", "cache_ttl",
                 "backup_interval", "replication_factor", "metadata")

    def __init__(self) -> None:
        self.database_url: str = "postgresql://localhost/ai_agent"
        self.redis_url: str = "redis://localhost:6379"
        self.vector_db_url: str = "http://localhost:6333"
        self.object_storage_url: str = "http://localhost:9000"
        self.enable_cache: bool = True
        self.enable_vector: bool = True
        self.enable_backup: bool = True
        self.enable_replication: bool = False
        self.pool_size: int = 20
        self.max_overflow: int = 10
        self.pool_timeout: int = 30
        self.cache_ttl: int = 3600
        self.backup_interval: int = 86400
        self.replication_factor: int = 1
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {s: getattr(self, s) for s in self.__slots__ if s != "metadata"}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersistenceConfiguration":
        c = cls()
        for k, v in data.items():
            if hasattr(c, k):
                setattr(c, k, v)
        return c

    def for_development(cls) -> "PersistenceConfiguration":
        c = cls()
        c.database_url = "sqlite:///dev.db"
        c.enable_replication = False
        c.enable_backup = False
        return c

    def for_production(cls) -> "PersistenceConfiguration":
        c = cls()
        c.pool_size = 50
        c.max_overflow = 20
        c.enable_replication = True
        c.enable_backup = True
        return c
