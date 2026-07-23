"""RedisClient — Enterprise Redis connection with retry, fallback, and metrics.

Features:
- Real Redis via redis-py (when available)
- In-memory fallback (when Redis server not running)
- Retry with exponential backoff
- Auto-reconnect on connection loss
- Connection pool metrics (active, idle, total operations, latency)
- TTL support with lazy expiration
- Pipeline support for batch operations
"""
from __future__ import annotations
import os
import time
import json
import threading
import fnmatch
from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class RedisConnectionConfig:
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str = ""
    max_connections: int = 50
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    retry_on_timeout: bool = True
    max_retries: int = 3
    retry_delays: tuple = (0.1, 0.5, 1.0)

    @classmethod
    def from_env(cls) -> "RedisConnectionConfig":
        return cls(
            host=os.environ.get("REDIS_HOST", "localhost"),
            port=int(os.environ.get("REDIS_PORT", "6379")),
            db=int(os.environ.get("REDIS_DB", "0")),
            password=os.environ.get("REDIS_PASSWORD", ""),
            max_connections=int(os.environ.get("REDIS_MAX_CONN", "50")),
        )


class RedisClient:
    """Enterprise Redis client with real Redis or in-memory fallback."""

    def __init__(self, config: Optional[RedisConnectionConfig] = None):
        self._config = config or RedisConnectionConfig.from_env()
        self._lock = threading.Lock()
        self._redis_available: Optional[bool] = None
        self._initialized = False
        self._redis_client = None

        # In-memory fallback store
        self._store: Dict[str, Any] = {}
        self._ttls: Dict[str, float] = {}
        self._hashes: Dict[str, Dict[str, str]] = {}
        self._lists: Dict[str, List[str]] = {}
        self._sets: Dict[str, set] = {}

        # Metrics
        self._total_ops = 0
        self._failed_ops = 0
        self._total_latency_ms = 0.0
        self._latencies: List[float] = []
        self._consecutive_failures = 0
        self._total_retries = 0
        self._last_error: Optional[str] = None

    def initialize(self) -> bool:
        """Initialize Redis connection. Returns True if real Redis is available."""
        if self._initialized:
            return self._redis_available or False

        try:
            import redis
            self._redis_client = redis.Redis(
                host=self._config.host,
                port=self._config.port,
                db=self._config.db,
                password=self._config.password or None,
                socket_timeout=self._config.socket_timeout,
                socket_connect_timeout=self._config.socket_connect_timeout,
                retry_on_timeout=self._config.retry_on_timeout,
                decode_responses=True,
            )
            self._redis_client.ping()
            self._redis_available = True
            self._initialized = True
            return True
        except (ImportError, Exception) as e:
            self._redis_available = False
            self._initialized = True
            self._last_error = str(e)[:200]
            return False

    def _auto_reconnect(self) -> bool:
        """Reconnect to Redis after failures."""
        try:
            if self._redis_client:
                self._redis_client.close()
        except Exception:
            pass
        self._initialized = False
        self._redis_available = None
        return self.initialize()

    def _execute_with_retry(self, fn, *args, **kwargs):
        """Execute operation with retry + auto-reconnect."""
        last_error = None
        delays = self._config.retry_delays

        for attempt in range(self._config.max_retries + 1):
            start = time.time()
            try:
                result = fn(*args, **kwargs)
                latency = (time.time() - start) * 1000

                with self._lock:
                    self._total_ops += 1
                    self._consecutive_failures = 0
                    self._latencies.append(latency)
                    if len(self._latencies) > 10000:
                        self._latencies = self._latencies[-5000:]
                    self._total_latency_ms += latency

                return result

            except Exception as e:
                last_error = e
                with self._lock:
                    self._failed_ops += 1
                    self._consecutive_failures += 1
                    self._last_error = str(e)[:200]

                if attempt < self._config.max_retries:
                    with self._lock:
                        self._total_retries += 1
                    delay = delays[min(attempt, len(delays) - 1)]
                    time.sleep(delay)

                    # Auto-reconnect after first failure
                    if attempt == 0 and self._redis_available:
                        self._auto_reconnect()

        raise last_error

    # ─── Key-Value Operations ─────────────────────────────────────

    def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.get, key)
        return self._memory_get(key)

    def set(self, key: str, value: str, ttl: float = 0.0) -> bool:
        """Set key-value pair with optional TTL in seconds."""
        if self._redis_available:
            if ttl > 0:
                self._execute_with_retry(self._redis_client.setex, key, int(ttl), value)
            else:
                self._execute_with_retry(self._redis_client.set, key, value)
            return True
        return self._memory_set(key, value, ttl)

    def delete(self, *keys: str) -> int:
        """Delete one or more keys. Returns count of deleted keys."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.delete, *keys)
        count = 0
        for k in keys:
            if self._memory_delete(k):
                count += 1
        return count

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.exists, key) > 0
        return self._memory_exists(key)

    def expire(self, key: str, ttl: float) -> bool:
        """Set TTL on existing key."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.expire, key, int(ttl))
        with self._lock:
            if key in self._store:
                self._ttls[key] = time.time() + ttl
                return True
            return False

    def ttl(self, key: str) -> float:
        """Get remaining TTL in seconds. -1 = no expiry, -2 = key not found."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.ttl, key)
        with self._lock:
            if key not in self._store:
                return -2
            if key not in self._ttls:
                return -1
            remaining = self._ttls[key] - time.time()
            return max(0, remaining)

    def keys(self, pattern: str = "*") -> List[str]:
        """Get all keys matching pattern."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.keys, pattern)
        with self._lock:
            self._memory_cleanup_expired()
            all_keys = set(self._store.keys()) | set(self._hashes.keys()) | set(self._lists.keys()) | set(self._sets.keys())
            return [k for k in all_keys if fnmatch.fnmatch(k, pattern)]

    def mget(self, keys: List[str]) -> List[Optional[str]]:
        """Get multiple values."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.mget, keys)
        return [self._memory_get(k) for k in keys]

    def mset(self, mapping: Dict[str, str]) -> bool:
        """Set multiple key-value pairs."""
        if self._redis_available:
            self._execute_with_retry(self._redis_client.mset, mapping)
            return True
        for k, v in mapping.items():
            self._memory_set(k, v)
        return True

    def incr(self, key: str) -> int:
        """Increment value by 1."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.incr, key)
        return self._memory_incr(key)

    def decr(self, key: str) -> int:
        """Decrement value by 1."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.decr, key)
        return self._memory_decr(key)

    def incrby(self, key: str, amount: int) -> int:
        """Increment value by amount."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.incrby, key, amount)
        val = int(self._store.get(key, 0)) + amount
        self._store[key] = str(val)
        return val

    # ─── Hash Operations ──────────────────────────────────────────

    def hset(self, name: str, key: str, value: str) -> int:
        """Set hash field."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.hset, name, key, value)
        with self._lock:
            if name not in self._hashes:
                self._hashes[name] = {}
            self._hashes[name][key] = value
            return 1

    def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field value."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.hget, name, key)
        with self._lock:
            return self._hashes.get(name, {}).get(key)

    def hgetall(self, name: str) -> Dict[str, str]:
        """Get all hash fields."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.hgetall, name)
        with self._lock:
            return dict(self._hashes.get(name, {}))

    def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.hdel, name, *keys)
        with self._lock:
            h = self._hashes.get(name, {})
            count = 0
            for k in keys:
                if k in h:
                    del h[k]
                    count += 1
            return count

    # ─── List Operations ──────────────────────────────────────────

    def lpush(self, key: str, *values: str) -> int:
        """Push values to list head."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.lpush, key, *values)
        with self._lock:
            if key not in self._lists:
                self._lists[key] = []
            for v in reversed(values):
                self._lists[key].insert(0, v)
            return len(self._lists[key])

    def rpush(self, key: str, *values: str) -> int:
        """Push values to list tail."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.rpush, key, *values)
        with self._lock:
            if key not in self._lists:
                self._lists[key] = []
            for v in values:
                self._lists[key].append(v)
            return len(self._lists[key])

    def lpop(self, key: str) -> Optional[str]:
        """Pop value from list head."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.lpop, key)
        with self._lock:
            lst = self._lists.get(key, [])
            if lst:
                return lst.pop(0)
            return None

    def rpop(self, key: str) -> Optional[str]:
        """Pop value from list tail."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.rpop, key)
        with self._lock:
            lst = self._lists.get(key, [])
            if lst:
                return lst.pop()
            return None

    def lrange(self, key: str, start: int, end: int) -> List[str]:
        """Get list range."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.lrange, key, start, end)
        with self._lock:
            lst = self._lists.get(key, [])
            if end == -1:
                return lst[start:]
            return lst[start:end + 1]

    def llen(self, key: str) -> int:
        """Get list length."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.llen, key)
        with self._lock:
            return len(self._lists.get(key, []))

    # ─── Set Operations ───────────────────────────────────────────

    def sadd(self, key: str, *values: str) -> int:
        """Add values to set."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.sadd, key, *values)
        with self._lock:
            if key not in self._sets:
                self._sets[key] = set()
            before = len(self._sets[key])
            self._sets[key].update(values)
            return len(self._sets[key]) - before

    def smembers(self, key: str) -> set:
        """Get all set members."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.smembers, key)
        with self._lock:
            return set(self._sets.get(key, set()))

    def srem(self, key: str, *values: str) -> int:
        """Remove values from set."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.srem, key, *values)
        with self._lock:
            s = self._sets.get(key, set())
            count = 0
            for v in values:
                if v in s:
                    s.discard(v)
                    count += 1
            return count

    def scard(self, key: str) -> int:
        """Get set cardinality."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.scard, key)
        with self._lock:
            return len(self._sets.get(key, set()))

    # ─── Pub/Sub (simplified) ─────────────────────────────────────

    def publish(self, channel: str, message: str) -> int:
        """Publish message to channel."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.publish, channel, message)
        # In-memory: just track
        return 1

    # ─── Pipeline ─────────────────────────────────────────────────

    def pipeline(self):
        """Create a pipeline for batch operations."""
        if self._redis_available:
            return self._redis_client.pipeline(transaction=False)
        return InMemoryPipeline(self)

    # ─── Server Operations ────────────────────────────────────────

    def ping(self) -> bool:
        """Ping server."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.ping)
        return self._initialized

    def dbsize(self) -> int:
        """Get number of keys."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.dbsize)
        with self._lock:
            self._cleanup_expired()
            return len(self._store) + len(self._hashes) + len(self._lists) + len(self._sets)

    def flushdb(self) -> bool:
        """Flush current database."""
        if self._redis_available:
            self._execute_with_retry(self._redis_client.flushdb)
            return True
        with self._lock:
            self._store.clear()
            self._ttls.clear()
            self._hashes.clear()
            self._lists.clear()
            self._sets.clear()
            return True

    def info(self) -> Dict[str, Any]:
        """Get server info."""
        if self._redis_available:
            return self._execute_with_retry(self._redis_client.info)
        return {
            "redis_version": "in-memory-fallback",
            "connected_clients": 1,
            "used_memory_human": "N/A",
            "role": "standalone",
        }

    # ─── Metrics ──────────────────────────────────────────────────

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive connection metrics."""
        lats = self._latencies
        avg_lat = sum(lats) / len(lats) if lats else 0.0
        sorted_lats = sorted(lats)
        p95 = sorted_lats[int(len(sorted_lats) * 0.95)] if len(sorted_lats) >= 2 else avg_lat
        p99 = sorted_lats[int(len(sorted_lats) * 0.99)] if len(sorted_lats) >= 2 else avg_lat

        return {
            "redis_available": self._redis_available,
            "initialized": self._initialized,
            "healthy": self.ping() if self._initialized else False,
            "total_ops": self._total_ops,
            "failed_ops": self._failed_ops,
            "total_retries": self._total_retries,
            "consecutive_failures": self._consecutive_failures,
            "last_error": self._last_error,
            "latency": {
                "avg_ms": round(avg_lat, 2),
                "p95_ms": round(p95, 2),
                "p99_ms": round(p99, 2),
                "total_latency_ms": round(self._total_latency_ms, 2),
                "samples": len(lats),
            },
            "config": {
                "host": self._config.host,
                "port": self._config.port,
                "db": self._config.db,
                "max_connections": self._config.max_connections,
            },
        }

    def close(self):
        """Close connection."""
        if self._redis_client:
            try:
                self._redis_client.close()
            except Exception:
                pass
        self._initialized = False

    # ─── In-Memory Fallback Methods ───────────────────────────────

    def _memory_cleanup_expired(self):
        """Remove expired keys from memory (caller must hold lock)."""
        now = time.time()
        expired = [k for k, exp in self._ttls.items() if now > exp]
        for k in expired:
            self._store.pop(k, None)
            self._ttls.pop(k, None)

    def _cleanup_expired(self):
        self._memory_cleanup_expired()

    def _memory_get(self, key: str) -> Optional[str]:
        self._memory_cleanup_expired()
        return self._store.get(key)

    def _memory_set(self, key: str, value: str, ttl: float = 0.0) -> bool:
        with self._lock:
            self._store[key] = value
            if ttl > 0:
                self._ttls[key] = time.time() + ttl
            return True

    def _memory_delete(self, key: str) -> bool:
        with self._lock:
            existed = key in self._store or key in self._hashes or key in self._lists or key in self._sets
            self._store.pop(key, None)
            self._ttls.pop(key, None)
            self._hashes.pop(key, None)
            self._lists.pop(key, None)
            self._sets.pop(key, None)
            return existed

    def _memory_exists(self, key: str) -> bool:
        with self._lock:
            self._memory_cleanup_expired()
            return key in self._store or key in self._hashes or key in self._lists or key in self._sets

    def _memory_incr(self, key: str) -> int:
        with self._lock:
            val = int(self._store.get(key, 0)) + 1
            self._store[key] = str(val)
            return val

    def _memory_decr(self, key: str) -> int:
        with self._lock:
            val = int(self._store.get(key, 0)) - 1
            self._store[key] = str(val)
            return val


class InMemoryPipeline:
    """In-memory pipeline for batch operations."""

    def __init__(self, client: RedisClient):
        self._client = client
        self._commands: List[tuple] = []

    def set(self, key: str, value: str, **kwargs):
        self._commands.append(("set", key, value, kwargs))
        return self

    def get(self, key: str):
        self._commands.append(("get", key))
        return self

    def delete(self, *keys):
        self._commands.append(("delete", keys))
        return self

    def execute(self) -> List[Any]:
        results = []
        for cmd in self._commands:
            op = cmd[0]
            if op == "set":
                self._client.set(cmd[1], cmd[2])
                results.append(True)
            elif op == "get":
                results.append(self._client.get(cmd[1]))
            elif op == "delete":
                results.append(self._client.delete(*cmd[1]))
        self._commands.clear()
        return results
