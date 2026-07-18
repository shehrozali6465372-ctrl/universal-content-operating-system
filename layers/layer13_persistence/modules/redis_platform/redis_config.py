"""redis_config.py — Redis configuration."""
from __future__ import annotations
from typing import Any, Dict


class RedisConfig:
    """Redis connection and behavior configuration."""

    __slots__ = ("host", "port", "db", "password", "max_connections",
                 "timeout", "retry_on_timeout", "ssl", "socket_timeout",
                 "socket_connect_timeout", "metadata")

    def __init__(self) -> None:
        self.host: str = "localhost"
        self.port: int = 6379
        self.db: int = 0
        self.password: str = ""
        self.max_connections: int = 50
        self.timeout: float = 5.0
        self.retry_on_timeout: bool = True
        self.ssl: bool = False
        self.socket_timeout: float = 5.0
        self.socket_connect_timeout: float = 5.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {s: getattr(self, s) for s in self.__slots__ if s != "metadata"}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RedisConfig":
        c = cls()
        for k, v in data.items():
            if hasattr(c, k):
                setattr(c, k, v)
        return c
