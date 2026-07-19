"""ConnectionPool — manage database connections with pooling."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional
from enum import Enum


class ConnectionState(str, Enum):
    IDLE = "idle"; ACTIVE = "active"; CLOSED = "closed"; ERROR = "error"


class PooledConnection:
    __slots__ = ("conn_id", "state", "created_at", "last_used", "use_count",
                 "config", "metadata")

    def __init__(self, conn_id: str, config: Dict[str, Any]) -> None:
        self.conn_id = conn_id
        self.state = ConnectionState.IDLE
        self.created_at = time.time()
        self.last_used = time.time()
        self.use_count = 0
        self.config = config
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"conn_id": self.conn_id, "state": self.state.value,
                "use_count": self.use_count}


class ConnectionPool:
    def __init__(self, min_size: int = 2, max_size: int = 10,
                 db_url: str = "") -> None:
        self._min_size = min_size
        self._max_size = max_size
        self._db_url = db_url
        self._connections: Dict[str, PooledConnection] = {}
        self._lock = threading.Lock()
        self._counter = 0

    def initialize(self) -> int:
        created = 0
        for _ in range(self._min_size):
            self._create_connection()
            created += 1
        return created

    def _create_connection(self) -> PooledConnection:
        self._counter += 1
        conn = PooledConnection(f"conn_{self._counter}", {"url": self._db_url})
        self._connections[conn.conn_id] = conn
        return conn

    def acquire(self, timeout: float = 5.0) -> Optional[PooledConnection]:
        with self._lock:
            for conn in self._connections.values():
                if conn.state == ConnectionState.IDLE:
                    conn.state = ConnectionState.ACTIVE
                    conn.last_used = time.time()
                    conn.use_count += 1
                    return conn
            if len(self._connections) < self._max_size:
                conn = self._create_connection()
                conn.state = ConnectionState.ACTIVE
                conn.use_count = 1
                return conn
        return None

    def release(self, conn: PooledConnection) -> bool:
        with self._lock:
            if conn.state == ConnectionState.ACTIVE:
                conn.state = ConnectionState.IDLE
                return True
        return False

    def close(self, conn_id: str) -> bool:
        with self._lock:
            conn = self._connections.get(conn_id)
            if conn:
                conn.state = ConnectionState.CLOSED
                return True
        return False

    def close_all(self) -> int:
        with self._lock:
            count = 0
            for conn in self._connections.values():
                conn.state = ConnectionState.CLOSED
                count += 1
            return count

    def stats(self) -> Dict[str, Any]:
        idle = sum(1 for c in self._connections.values() if c.state == ConnectionState.IDLE)
        active = sum(1 for c in self._connections.values() if c.state == ConnectionState.ACTIVE)
        return {"total": len(self._connections), "idle": idle, "active": active,
                "min_size": self._min_size, "max_size": self._max_size}

    def list_connections(self) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self._connections.values()]
