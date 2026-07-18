"""pubsub.py — Redis Pub/Sub implementation."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List
from collections import defaultdict


class PubSubMessage:
    """A pub/sub message."""
    __slots__ = ("channel", "data", "timestamp")
    _counter = 0

    def __init__(self, channel: str, data: str) -> None:
        PubSubMessage._counter += 1
        self.channel = channel
        self.data = data
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"channel": self.channel, "data": self.data,
                "timestamp": self.timestamp}


class PubSub:
    """Redis-style Pub/Sub implementation."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._messages: Dict[str, List[PubSubMessage]] = defaultdict(list)
        self._total_published: int = 0

    def subscribe(self, channel: str, callback: Callable) -> None:
        self._subscribers[channel].append(callback)

    def unsubscribe(self, channel: str, callback: Callable) -> bool:
        if channel in self._subscribers:
            self._subscribers[channel] = [c for c in self._subscribers[channel] if c != callback]
            return True
        return False

    def publish(self, channel: str, data: str) -> int:
        msg = PubSubMessage(channel, data)
        self._messages[channel].append(msg)
        self._total_published += 1
        count = 0
        for callback in self._subscribers.get(channel, []):
            try:
                callback(msg)
                count += 1
            except Exception:
                pass
        return count

    def get_messages(self, channel: str, limit: int = 100) -> List[PubSubMessage]:
        return self._messages.get(channel, [])[-limit:]

    def subscriber_count(self, channel: str) -> int:
        return len(self._subscribers.get(channel, []))

    def channel_count(self) -> int:
        return len(self._subscribers)

    def stats(self) -> Dict[str, Any]:
        return {"channels": self.channel_count(),
                "total_published": self._total_published}
