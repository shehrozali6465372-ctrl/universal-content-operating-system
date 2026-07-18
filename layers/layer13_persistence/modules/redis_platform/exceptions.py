"""Exceptions for Redis platform."""
from __future__ import annotations

class RedisError(Exception):
    """Base Redis error."""

class ConnectionError(RedisError):
    """Connection failed."""

class CommandError(RedisError):
    """Command failed."""

class SerializationError(RedisError):
    """Serialization failed."""

class PubSubError(RedisError):
    """PubSub error."""

class ClusterError(RedisError):
    """Cluster error."""

class LockError(RedisError):
    """Lock error."""

class QueueError(RedisError):
    """Queue error."""
