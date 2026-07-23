"""RedisPubSub — Real-time event messaging with channels and subscribers.

Features:
- Publish messages to channels
- Subscribe to channels with callbacks
- Pattern-based subscriptions (e.g., "events.*")
- Message history (last N messages per channel)
- Event filtering by type
"""
from __future__ import annotations
import json
import time
import threading
from typing import Any, Callable, Dict, List, Optional
from collections import defaultdict


class RedisPubSub:
    """Publish-subscribe messaging system backed by Redis."""

    def __init__(self, client: Any, history_size: int = 100):
        self._client = client
        self._history_size = history_size
        self._prefix = "pubsub"

        # In-memory subscriber management
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._pattern_subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.Lock()
        self._channels: set = set()

        # Stats
        self._published = 0
        self._delivered = 0

    def _history_key(self, channel: str) -> str:
        return f"{self._prefix}:history:{channel}"

    def publish(self, channel: str, message: Any, event_type: str = "message") -> int:
        """Publish a message to a channel.

        Returns number of subscribers notified.
        """
        now = time.time()

        # Serialize message
        if isinstance(message, (dict, list)):
            payload = json.dumps(message, default=str)
        else:
            payload = str(message)

        # Track channel
        with self._lock:
            self._channels.add(channel)

        # Store in history (sorted set via list)
        history_key = self._history_key(channel)
        entry = json.dumps({
            "payload": payload,
            "event_type": event_type,
            "timestamp": now,
        }, default=str)

        # Use rpush + ltrim to maintain fixed-size history
        self._client.rpush(history_key, entry)
        # Keep only last N messages
        all_msgs = self._client.lrange(history_key, 0, -1)
        if len(all_msgs) > self._history_size:
            # Trim to last N
            trimmed = all_msgs[-self._history_size:]
            self._client.delete(history_key)
            for msg in trimmed:
                self._client.rpush(history_key, msg)
        self._client.expire(history_key, 86400)  # 24h TTL

        # Deliver to direct subscribers
        delivered = 0
        with self._lock:
            for callback in self._subscribers.get(channel, []):
                try:
                    callback(channel, payload, event_type, now)
                    delivered += 1
                except Exception:
                    pass

            # Deliver to pattern subscribers
            for pattern, callbacks in self._pattern_subscribers.items():
                import fnmatch
                if fnmatch.fnmatch(channel, pattern):
                    for callback in callbacks:
                        try:
                            callback(channel, payload, event_type, now)
                            delivered += 1
                        except Exception:
                            pass

        self._published += 1
        self._delivered += delivered
        return delivered

    def subscribe(self, channel: str, callback: Callable) -> None:
        """Subscribe to a channel with a callback."""
        with self._lock:
            self._subscribers[channel].append(callback)

    def subscribe_pattern(self, pattern: str, callback: Callable) -> None:
        """Subscribe to channels matching a pattern."""
        with self._lock:
            self._pattern_subscribers[pattern].append(callback)

    def unsubscribe(self, channel: str, callback: Callable = None) -> None:
        """Unsubscribe from a channel."""
        with self._lock:
            if callback:
                if channel in self._subscribers:
                    self._subscribers[channel] = [
                        cb for cb in self._subscribers[channel] if cb != callback
                    ]
            else:
                self._subscribers.pop(channel, None)

    def get_history(self, channel: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get message history for a channel."""
        history_key = self._history_key(channel)
        messages = self._client.lrange(history_key, -limit, -1)
        result = []
        for msg in messages:
            try:
                parsed = json.loads(msg)
                result.append(parsed)
            except (json.JSONDecodeError, TypeError):
                result.append({"payload": msg, "event_type": "message", "timestamp": 0})
        return result

    def get_channels(self) -> List[str]:
        """Get all channels with history."""
        with self._lock:
            return list(self._channels)

    def get_subscriber_count(self, channel: str) -> int:
        """Get number of subscribers for a channel."""
        with self._lock:
            return len(self._subscribers.get(channel, []))

    def get_stats(self) -> Dict[str, Any]:
        """Get pub/sub statistics."""
        with self._lock:
            total_subs = sum(len(subs) for subs in self._subscribers.values())
            total_pattern_subs = sum(len(subs) for subs in self._pattern_subscribers.values())
            channel_count = len(self._channels)
            return {
                "total_published": self._published,
                "total_delivered": self._delivered,
                "channels_with_history": channel_count,
                "direct_subscribers": total_subs,
                "pattern_subscribers": total_pattern_subs,
            }
