"""EventBridge — cross-layer event propagation system."""
from __future__ import annotations
import time
import uuid
from typing import Any, Callable, Dict, List, Optional


class Event:
    __slots__ = ("event_id", "event_type", "source", "data", "timestamp", "metadata")

    def __init__(self, event_type: str, source: str = "",
                 data: Optional[Dict[str, Any]] = None) -> None:
        self.event_id = str(uuid.uuid4())[:12]
        self.event_type = event_type
        self.source = source
        self.data = data or {}
        self.timestamp = time.time()
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "event_type": self.event_type,
                "source": self.source, "timestamp": self.timestamp}


class EventSubscription:
    __slots__ = ("subscription_id", "event_type", "handler", "source_filter", "active")

    def __init__(self, subscription_id: str, event_type: str,
                 handler: Callable, source_filter: Optional[str] = None) -> None:
        self.subscription_id = subscription_id
        self.event_type = event_type
        self.handler = handler
        self.source_filter = source_filter
        self.active = True


class EventBridge:
    def __init__(self) -> None:
        self._subscriptions: Dict[str, List[EventSubscription]] = {}
        self._wildcard_subscriptions: List[EventSubscription] = []
        self._history: List[Dict[str, Any]] = []
        self._subscription_counter = 0

    def subscribe(self, event_type: str, handler: Callable,
                  source_filter: Optional[str] = None) -> str:
        self._subscription_counter += 1
        sub_id = f"sub_{self._subscription_counter}"
        sub = EventSubscription(sub_id, event_type, handler, source_filter)
        if event_type == "*":
            self._wildcard_subscriptions.append(sub)
        else:
            if event_type not in self._subscriptions:
                self._subscriptions[event_type] = []
            self._subscriptions[event_type].append(sub)
        return sub_id

    def unsubscribe(self, subscription_id: str) -> bool:
        for event_type, subs in self._subscriptions.items():
            self._subscriptions[event_type] = [s for s in subs if s.subscription_id != subscription_id]
        self._wildcard_subscriptions = [s for s in self._wildcard_subscriptions
                                        if s.subscription_id != subscription_id]
        return True

    def publish(self, event: Event) -> Dict[str, Any]:
        delivered = 0
        errors = []
        subs = self._subscriptions.get(event.event_type, []) + self._wildcard_subscriptions
        for sub in subs:
            if not sub.active:
                continue
            if sub.source_filter and event.source != sub.source_filter:
                continue
            try:
                sub.handler(event)
                delivered += 1
            except Exception as exc:
                errors.append({"subscription": sub.subscription_id, "error": str(exc)})
        self._history.append({**event.to_dict(), "delivered": delivered, "errors": len(errors)})
        return {"delivered": delivered, "errors": errors, "event_id": event.event_id}

    def emit(self, event_type: str, source: str = "",
             data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        event = Event(event_type, source, data)
        return self.publish(event)

    def list_subscriptions(self) -> List[Dict[str, Any]]:
        result = []
        for event_type, subs in self._subscriptions.items():
            for sub in subs:
                result.append({"subscription_id": sub.subscription_id,
                               "event_type": event_type, "active": sub.active})
        for sub in self._wildcard_subscriptions:
            result.append({"subscription_id": sub.subscription_id,
                           "event_type": "*", "active": sub.active})
        return result

    def get_history(self, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if event_type:
            return [h for h in self._history if h.get("event_type") == event_type]
        return list(self._history)

    def clear_history(self) -> None:
        self._history.clear()
