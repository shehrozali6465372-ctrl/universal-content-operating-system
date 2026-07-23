"""RedisManager — Enterprise Redis manager integrating all components.

Features:
- Connection pool with retry + auto-reconnect
- Cache layer (namespace-scoped, tag-based)
- Session management
- Rate limiting (sliding window + token bucket)
- Pub/Sub messaging
- Task queue (priority-based with retry)
- Health monitoring
- Performance metrics
- Database statistics (--redis-status)
"""
from __future__ import annotations
import os
import json
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime, timezone

from layers.layer13_persistence.modules.redis_platform.redis_client import RedisClient, RedisConnectionConfig
from layers.layer13_persistence.modules.redis_platform.redis_cache import RedisCache
from layers.layer13_persistence.modules.redis_platform.redis_session import RedisSession
from layers.layer13_persistence.modules.redis_platform.redis_rate_limiter import RedisRateLimiter
from layers.layer13_persistence.modules.redis_platform.redis_pubsub import RedisPubSub
from layers.layer13_persistence.modules.redis_platform.redis_queue import RedisQueue


class RedisManager:
    """Main Redis manager with full enterprise features."""

    def __init__(self, config: Optional[RedisConnectionConfig] = None):
        self._config = config or RedisConnectionConfig.from_env()
        self._client: Optional[RedisClient] = None
        self._initialized = False

        # Components (initialized on initialize())
        self.cache: Optional[RedisCache] = None
        self.sessions: Optional[RedisSession] = None
        self.rate_limiter: Optional[RedisRateLimiter] = None
        self.pubsub: Optional[RedisPubSub] = None
        self.queues: Dict[str, RedisQueue] = {}

    def initialize(self) -> bool:
        """Initialize Redis and all components."""
        if self._initialized:
            return True

        self._client = RedisClient(self._config)
        redis_available = self._client.initialize()

        # Initialize all components
        self.cache = RedisCache(self._client, namespace="aios")
        self.sessions = RedisSession(self._client, session_ttl=3600.0)
        self.rate_limiter = RedisRateLimiter(self._client)
        self.pubsub = RedisPubSub(self._client)

        self._initialized = True
        return redis_available

    def get_queue(self, name: str = "default") -> RedisQueue:
        """Get or create a named queue."""
        if name not in self.queues:
            self.queues[name] = RedisQueue(self._client, name=name)
        return self.queues[name]

    # ─── Cache Shortcuts ──────────────────────────────────────────

    def cache_get(self, key: str) -> Optional[Any]:
        """Get from cache."""
        return self.cache.get(key) if self.cache else None

    def cache_set(self, key: str, value: Any, ttl: float = 300.0, tags: List[str] = None) -> bool:
        """Set in cache."""
        return self.cache.set(key, value, ttl=ttl, tags=tags) if self.cache else False

    def cache_delete(self, key: str) -> bool:
        """Delete from cache."""
        return self.cache.delete(key) if self.cache else False

    # ─── Session Shortcuts ────────────────────────────────────────

    def create_session(self, user_id: str, platform: str, context: Dict = None) -> Dict:
        """Create a user session."""
        return self.sessions.create(user_id, platform, context) if self.sessions else {}

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID."""
        return self.sessions.get(session_id) if self.sessions else None

    # ─── Rate Limit Shortcuts ─────────────────────────────────────

    def check_rate_limit(self, identifier: str, max_requests: int,
                         window_seconds: float = 60.0) -> Tuple[bool, Dict]:
        """Check rate limit."""
        if self.rate_limiter:
            return self.rate_limiter.sliding_window(identifier, max_requests, window_seconds)
        return True, {"allowed": True, "remaining": max_requests}

    # ─── Pub/Sub Shortcuts ────────────────────────────────────────

    def publish_event(self, channel: str, message: Any, event_type: str = "message") -> int:
        """Publish an event."""
        return self.pubsub.publish(channel, message, event_type) if self.pubsub else 0

    def subscribe_event(self, channel: str, callback: Callable) -> None:
        """Subscribe to events."""
        if self.pubsub:
            self.pubsub.subscribe(channel, callback)

    # ─── Queue Shortcuts ──────────────────────────────────────────

    def enqueue_task(self, task_type: str, payload: Dict, queue: str = "default",
                     priority: str = "normal") -> str:
        """Enqueue a task."""
        q = self.get_queue(queue)
        return q.enqueue(task_type, payload, priority=priority)

    def dequeue_task(self, queue: str = "default") -> Optional[Dict]:
        """Dequeue next task."""
        q = self.get_queue(queue)
        return q.dequeue()

    # ─── Health & Status ──────────────────────────────────────────

    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check."""
        client_healthy = self._client.ping() if self._client else False

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "initialized": self._initialized,
            "redis_available": self._client._redis_available if self._client else False,
            "client_healthy": client_healthy,
            "overall": "healthy" if client_healthy else "degraded",
        }

    def get_redis_status(self) -> Dict[str, Any]:
        """Get comprehensive Redis status — for --redis-status command."""
        metrics = self._client.get_metrics() if self._client else {}
        cache_stats = self.cache.get_stats() if self.cache else {}
        session_stats = self.sessions.get_stats() if self.sessions else {}
        rate_stats = self.rate_limiter.get_stats() if self.rate_limiter else {}
        pubsub_stats = self.pubsub.get_stats() if self.pubsub else {}

        # Queue stats
        queue_stats = {}
        for name, queue in self.queues.items():
            queue_stats[name] = queue.get_stats()

        overall = "Healthy" if metrics.get("healthy", False) else "Degraded"

        return {
            "overall": overall,
            "connection": {
                "redis_available": metrics.get("redis_available", False),
                "healthy": metrics.get("healthy", False),
                "total_ops": metrics.get("total_ops", 0),
                "failed_ops": metrics.get("failed_ops", 0),
                "total_retries": metrics.get("total_retries", 0),
                "consecutive_failures": metrics.get("consecutive_failures", 0),
            },
            "latency": metrics.get("latency", {}),
            "cache": cache_stats,
            "sessions": session_stats,
            "rate_limiter": rate_stats,
            "pubsub": pubsub_stats,
            "queues": queue_stats,
            "config": metrics.get("config", {}),
            "initialized": self._initialized,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics."""
        return {
            "initialized": self._initialized,
            "cache": self.cache.get_stats() if self.cache else {},
            "sessions": self.sessions.get_stats() if self.sessions else {},
            "rate_limiter": self.rate_limiter.get_stats() if self.rate_limiter else {},
            "pubsub": self.pubsub.get_stats() if self.pubsub else {},
            "queues": {name: q.get_stats() for name, q in self.queues.items()},
        }

    def close(self):
        """Close all connections."""
        if self._client:
            self._client.close()
        self._initialized = False


# Singleton
_redis_instance: Optional[RedisManager] = None


def get_redis(config: Optional[RedisConnectionConfig] = None) -> RedisManager:
    """Get or create Redis manager singleton."""
    global _redis_instance
    if _redis_instance is None:
        _redis_instance = RedisManager(config)
        _redis_instance.initialize()
    return _redis_instance
