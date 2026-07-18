"""connection_manager.py — Database connection management."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class DatabaseConnection:
    """Single database connection."""
    __slots__ = ("conn_id", "database", "host", "port", "user", "is_active",
                 "created_at", "last_used", "metadata")
    _counter = 0

    def __init__(self, database: str, host: str = "localhost", port: int = 5432,
                 user: str = "postgres") -> None:
        DatabaseConnection._counter += 1
        self.conn_id: int = DatabaseConnection._counter
        self.database = database
        self.host = host
        self.port = port
        self.user = user
        self.is_active: bool = True
        self.created_at: float = time.time()
        self.last_used: float = time.time()
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"conn_id": self.conn_id, "database": self.database,
                "host": self.host, "port": self.port, "active": self.is_active}


class ConnectionManager:
    """Manages database connections."""

    def __init__(self) -> None:
        self._connections: Dict[str, DatabaseConnection] = {}
        self._config: Dict[str, Any] = {}

    def configure(self, database: str, host: str = "localhost", port: int = 5432,
                  user: str = "postgres") -> None:
        self._config = {"database": database, "host": host, "port": port, "user": user}

    def connect(self, name: str = "default") -> DatabaseConnection:
        cfg = self._config or {"database": "default", "host": "localhost",
                                "port": 5432, "user": "postgres"}
        conn = DatabaseConnection(cfg.get("database", name), cfg.get("host", "localhost"),
                                   cfg.get("port", 5432), cfg.get("user", "postgres"))
        self._connections[name] = conn
        return conn

    def disconnect(self, name: str = "default") -> bool:
        conn = self._connections.pop(name, None)
        if conn:
            conn.is_active = False
            return True
        return False

    def disconnect_all(self) -> int:
        count = len(self._connections)
        for conn in self._connections.values():
            conn.is_active = False
        self._connections.clear()
        return count

    def get_connection(self, name: str = "default") -> Optional[DatabaseConnection]:
        return self._connections.get(name)

    def get_active(self) -> List[DatabaseConnection]:
        return [c for c in self._connections.values() if c.is_active]

    def count(self) -> int:
        return len(self._connections)

    def is_connected(self, name: str = "default") -> bool:
        conn = self._connections.get(name)
        return conn is not None and conn.is_active

    def to_dict(self) -> Dict[str, Any]:
        return {"config": dict(self._config), "connections": len(self._connections),
                "active": len(self.get_active())}
