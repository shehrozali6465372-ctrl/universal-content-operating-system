"""UsageAnalytics — track API and feature usage patterns."""
from __future__ import annotations
import time
import uuid
from typing import Any, Dict, List, Optional
from collections import defaultdict


class UsageEvent:
    __slots__ = ("event_id", "event_type", "user_id", "resource",
                 "action", "duration_ms", "timestamp", "metadata")

    def __init__(self, event_type: str, user_id: str = "", resource: str = "",
                 action: str = "") -> None:
        self.event_id = str(uuid.uuid4())[:8]
        self.event_type = event_type
        self.user_id = user_id
        self.resource = resource
        self.action = action
        self.duration_ms: float = 0.0
        self.timestamp = time.time()
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "type": self.event_type,
                "user_id": self.user_id, "resource": self.resource,
                "timestamp": self.timestamp}


class UsageAnalytics:
    def __init__(self) -> None:
        self._events: List[UsageEvent] = []
        self._counts: Dict[str, int] = defaultdict(int)
        self._user_counts: Dict[str, int] = defaultdict(int)

    def track(self, event_type: str, user_id: str = "", resource: str = "",
              action: str = "") -> UsageEvent:
        event = UsageEvent(event_type, user_id, resource, action)
        self._events.append(event)
        self._counts[event_type] += 1
        if user_id:
            self._user_counts[user_id] += 1
        return event

    def get_counts(self, event_type: Optional[str] = None) -> Dict[str, int]:
        if event_type:
            return {event_type: self._counts.get(event_type, 0)}
        return dict(self._counts)

    def get_user_activity(self, user_id: str) -> int:
        return self._user_counts.get(user_id, 0)

    def get_top_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        sorted_users = sorted(self._user_counts.items(), key=lambda x: -x[1])
        return [{"user_id": u, "events": c} for u, c in sorted_users[:limit]]

    def list_events(self, event_type: Optional[str] = None,
                    limit: int = 100) -> List[Dict[str, Any]]:
        events = self._events
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return [e.to_dict() for e in events[-limit:]]

    def summary(self) -> Dict[str, Any]:
        return {"total_events": len(self._events), "event_types": dict(self._counts),
                "unique_users": len(self._user_counts)}
