"""Bounded usage analytics with thread-safe counters."""
from __future__ import annotations

import threading
import time
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Optional


class UsageEvent:
    __slots__ = ("event_id", "event_type", "user_id", "resource", "action",
                 "duration_ms", "timestamp", "metadata")

    def __init__(self, event_type: str, user_id: str = "", resource: str = "", action: str = "") -> None:
        self.event_id = str(uuid.uuid4())
        self.event_type, self.user_id = event_type, user_id
        self.resource, self.action = resource, action
        self.duration_ms = 0.0
        self.timestamp = time.time()
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "type": self.event_type, "user_id": self.user_id,
                "resource": self.resource, "action": self.action,
                "timestamp": self.timestamp, "duration_ms": self.duration_ms}


class UsageAnalytics:
    def __init__(self, history_size: int = 10000) -> None:
        if history_size <= 0:
            raise ValueError("history_size must be positive")
        self._lock = threading.RLock()
        self._history_size = history_size
        self._events: List[UsageEvent] = []
        self._counts: Dict[str, int] = defaultdict(int)
        self._user_counts: Dict[str, int] = defaultdict(int)

    def track(self, event_type: str, user_id: str = "", resource: str = "", action: str = "") -> UsageEvent:
        if not event_type.strip():
            raise ValueError("event_type is required")
        event = UsageEvent(event_type, user_id, resource, action)
        with self._lock:
            self._events.append(event)
            self._counts[event_type] += 1
            if user_id:
                self._user_counts[user_id] += 1
            if len(self._events) > self._history_size:
                del self._events[:-self._history_size]
        return event

    def get_counts(self, event_type: Optional[str] = None) -> Dict[str, int]:
        with self._lock:
            return {event_type: self._counts.get(event_type, 0)} if event_type else dict(self._counts)

    def get_user_activity(self, user_id: str) -> int:
        with self._lock:
            return self._user_counts.get(user_id, 0)

    def get_top_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        with self._lock:
            users = sorted(self._user_counts.items(), key=lambda item: (-item[1], item[0]))
            return [{"user_id": user, "events": count} for user, count in users[:limit]]

    def list_events(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        with self._lock:
            events = list(self._events)
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return [e.to_dict() for e in events[-limit:]]

    def summary(self) -> Dict[str, Any]:
        with self._lock:
            return {"total_events": len(self._events), "event_types": dict(self._counts),
                    "unique_users": len(self._user_counts)}
