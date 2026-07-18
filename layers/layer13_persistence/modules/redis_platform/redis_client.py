"""redis_client.py — Redis client abstraction."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class RedisClient:
    """Redis client with connection management."""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0,
                 password: str = "") -> None:
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._store: Dict[str, Any] = {}
        self._connected: bool = False
        self._ttl: Dict[str, float] = {}

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> bool:
        self._connected = False
        return True

    def is_connected(self) -> bool:
        return self._connected

    def get(self, key: str) -> Optional[str]:
        if key in self._ttl and time.time() > self._ttl[key]:
            del self._store[key]
            del self._ttl[key]
            return None
        return self._store.get(key)

    def set(self, key: str, value: str, ttl: float = 0.0) -> bool:
        self._store[key] = value
        if ttl > 0:
            self._ttl[key] = time.time() + ttl
        return True

    def delete(self, key: str) -> bool:
        self._store.pop(key, None)
        self._ttl.pop(key, None)
        return True

    def exists(self, key: str) -> bool:
        return key in self._store

    def keys(self, pattern: str = "*") -> List[str]:
        import fnmatch
        return [k for k in self._store if fnmatch.fnmatch(k, pattern)]

    def mget(self, keys: List[str]) -> List[Optional[str]]:
        return [self.get(k) for k in keys]

    def mset(self, mapping: Dict[str, str]) -> bool:
        for k, v in mapping.items():
            self._store[k] = v
        return True

    def incr(self, key: str) -> int:
        val = int(self._store.get(key, 0)) + 1
        self._store[key] = str(val)
        return val

    def decr(self, key: str) -> int:
        val = int(self._store.get(key, 0)) - 1
        self._store[key] = str(val)
        return val

    def flush(self) -> bool:
        self._store.clear()
        self._ttl.clear()
        return True

    def dbsize(self) -> int:
        return len(self._store)

    def ping(self) -> bool:
        return self._connected

    def to_dict(self) -> Dict[str, Any]:
        return {"host": self._host, "port": self._port, "db": self._db,
                "connected": self._connected, "keys": self.dbsize()}
