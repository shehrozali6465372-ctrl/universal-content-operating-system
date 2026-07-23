"""RedisCache — Intelligent caching layer with namespaces, tags, and stats.

Features:
- Namespace-scoped keys (prevents collisions)
- Tag-based invalidation (clear all keys with a tag)
- Cache-aside pattern (get_or_set)
- Cache statistics (hits, misses, evictions)
- JSON serialization for complex objects
- Pattern-based key scanning
"""
from __future__ import annotations
import json
import time
import threading
from typing import Any, Callable, Dict, List, Optional


class RedisCache:
    """Intelligent caching layer on top of RedisClient."""

    def __init__(self, client: Any, namespace: str = "cache"):
        self._client = client
        self._namespace = namespace
        self._lock = threading.Lock()

        # Stats
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._deletes = 0
        self._tag_invalidations = 0

    def _key(self, key: str) -> str:
        """Prefix key with namespace."""
        return f"{self._namespace}:{key}"

    def _tag_key(self, tag: str) -> str:
        """Key for tag index."""
        return f"{self._namespace}:_tags:{tag}"

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache. Returns None on miss."""
        full_key = self._key(key)
        raw = self._client.get(full_key)
        if raw is not None:
            with self._lock:
                self._hits += 1
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return raw
        with self._lock:
            self._misses += 1
        return None

    def set(self, key: str, value: Any, ttl: float = 300.0, tags: List[str] = None) -> bool:
        """Set value in cache with optional TTL and tags."""
        full_key = self._key(key)
        try:
            serialized = json.dumps(value, default=str)
        except (TypeError, ValueError):
            serialized = str(value)

        result = self._client.set(full_key, serialized, ttl=ttl)
        if result:
            with self._lock:
                self._sets += 1

            # Index under tags
            if tags:
                for tag in tags:
                    tag_key = self._tag_key(tag)
                    self._client.sadd(tag_key, full_key)
                    # Set same TTL on tag key
                    self._client.expire(tag_key, ttl + 60)

        return result

    def get_or_set(self, key: str, factory: Callable[[], Any], ttl: float = 300.0,
                   tags: List[str] = None) -> Any:
        """Cache-aside: get from cache, or compute and cache."""
        value = self.get(key)
        if value is not None:
            return value
        value = factory()
        self.set(key, value, ttl=ttl, tags=tags)
        return value

    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        full_key = self._key(key)
        result = self._client.delete(full_key) > 0
        if result:
            with self._lock:
                self._deletes += 1
        return result

    def invalidate_tag(self, tag: str) -> int:
        """Delete all keys with a specific tag."""
        tag_key = self._tag_key(tag)
        members = self._client.smembers(tag_key)
        count = 0
        for member in members:
            if self._client.delete(member):
                count += 1
        self._client.delete(tag_key)
        with self._lock:
            self._tag_invalidations += 1
        return count

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self._client.exists(self._key(key))

    def keys(self, pattern: str = "*") -> List[str]:
        """Get all cache keys matching pattern."""
        full_pattern = self._key(pattern)
        raw_keys = self._client.keys(full_pattern)
        prefix = self._namespace + ":"
        return [k[len(prefix):] if k.startswith(prefix) else k for k in raw_keys
                if not k.endswith(":_tags")]

    def clear(self) -> bool:
        """Clear all keys in this namespace."""
        all_keys = self._client.keys(self._key("*"))
        for k in all_keys:
            self._client.delete(k)
        # Clear tag indexes
        tag_keys = self._client.keys(self._key("_tags:*"))
        for k in tag_keys:
            self._client.delete(k)
        return True

    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values at once."""
        full_keys = [self._key(k) for k in keys]
        values = self._client.mget(full_keys)
        result = {}
        for key, val in zip(keys, values):
            if val is not None:
                try:
                    result[key] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    result[key] = val
                with self._lock:
                    self._hits += 1
            else:
                with self._lock:
                    self._misses += 1
        return result

    def set_many(self, mapping: Dict[str, Any], ttl: float = 300.0) -> bool:
        """Set multiple key-value pairs."""
        serialized = {}
        for key, value in mapping.items():
            try:
                serialized[self._key(key)] = json.dumps(value, default=str)
            except (TypeError, ValueError):
                serialized[self._key(key)] = str(value)
        return self._client.mset(serialized)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total = self._hits + self._misses
        return {
            "namespace": self._namespace,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_pct": round(self._hits / total * 100, 1) if total > 0 else 0.0,
            "sets": self._sets,
            "deletes": self._deletes,
            "tag_invalidations": self._tag_invalidations,
            "total_requests": total,
        }

    def reset_stats(self) -> None:
        """Reset all counters."""
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._sets = 0
            self._deletes = 0
            self._tag_invalidations = 0
