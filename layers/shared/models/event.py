"""
Shared Event Models
Frozen interface — v1.0.0

Used by the Global Event Bus for cross-layer communication.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class EventType(str, Enum):
    """Event types for the global event bus."""

    # Research events
    RESEARCH_STARTED = "research.started"
    RESEARCH_COMPLETED = "research.completed"
    RESEARCH_FAILED = "research.failed"
    TOPIC_DISCOVERED = "topic.discovered"
    TOPIC_SCORED = "topic.scored"
    TOPIC_SELECTED = "topic.selected"

    # Content events
    CONTENT_DRAFTED = "content.drafted"
    CONTENT_APPROVED = "content.approved"
    CONTENT_REJECTED = "content.rejected"
    CONTENT_SCHEDULED = "content.scheduled"

    # Publishing events
    POST_PUBLISHED = "post.published"
    POST_FAILED = "post.failed"
    POST_ENGAGEMENT = "post.engagement"

    # Analytics events
    ANALYTICS_COLLECTED = "analytics.collected"
    PERFORMANCE_ALERT = "performance.alert"
    TREND_DETECTED = "trend.detected"

    # Learning events
    LEARNING_UPDATED = "learning.updated"
    STRATEGY_CHANGED = "strategy.changed"
    IMPROVEMENT_DETECTED = "improvement.detected"

    # System events
    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"
    ERROR_OCCURRED = "error.occurred"
    CONFIG_CHANGED = "config.changed"


class Event:
    """An event published to the global event bus."""

    __slots__ = (
        "event_id", "event_type", "source",
        "data", "timestamp", "metadata",
    )

    def __init__(
        self,
        event_type: EventType,
        source: str = "",
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.event_id = f"evt_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        self.event_type = event_type
        self.source = source
        self.data = data or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value if isinstance(self.event_type, EventType) else self.event_type,
            "source": self.source,
            "data": dict(self.data),
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        event_type = data.get("event_type", "")
        if isinstance(event_type, str):
            try:
                event_type = EventType(event_type)
            except ValueError:
                pass
        e = cls(
            event_type=event_type,
            source=data.get("source", ""),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
        )
        e.event_id = data.get("event_id", e.event_id)
        e.timestamp = data.get("timestamp", e.timestamp)
        return e

    def __repr__(self) -> str:
        return f"Event(type={self.event_type}, source='{self.source}')"
