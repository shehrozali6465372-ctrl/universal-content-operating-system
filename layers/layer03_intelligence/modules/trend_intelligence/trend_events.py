"""Trend Events - Domain-specific events for trend lifecycle."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional


class TrendEvent:
    """A domain event for trend lifecycle."""
    __slots__ = ("event_type", "topic", "timestamp", "data", "source")

    def __init__(self, event_type: str = "", topic: str = "",
                 data: Optional[Dict] = None, source: str = "trend_intelligence"):
        self.event_type = event_type
        self.topic = topic
        self.timestamp = time.time()
        self.data = data or {}
        self.source = source

    def to_dict(self) -> Dict:
        return {
            "event_type": self.event_type, "topic": self.topic,
            "timestamp": self.timestamp, "data": dict(self.data),
            "source": self.source,
        }


# Event types
TREND_DETECTED = "trend.detected"
TREND_UPDATED = "trend.updated"
TREND_EXPIRED = "trend.expired"
TREND_PREDICTION_CHANGED = "trend.prediction.changed"
TREND_MOMENTUM_CHANGED = "trend.momentum.changed"
TREND_VIRALITY_SPIKE = "trend.virality.spike"
TREND_LIFECYCLE_CHANGED = "trend.lifecycle.changed"
TREND_CONFIDENCE_LOW = "trend.confidence.low"


class TrendEventBus:
    """Simple event bus for trend domain events."""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Callable]] = {}
        self._event_log: List[TrendEvent] = []
        self._max_log = 1000

    def subscribe(self, event_type: str, handler: Callable) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        if event_type in self._handlers:
            self._handlers[event_type] = [h for h in self._handlers[event_type] if h != handler]

    def publish(self, event: TrendEvent) -> None:
        self._event_log.append(event)
        if len(self._event_log) > self._max_log:
            self._event_log = self._event_log[-self._max_log:]

        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                pass  # Don't let handler errors break the bus

    def publish_batch(self, events: List[TrendEvent]) -> None:
        for event in events:
            self.publish(event)

    def get_recent_events(self, n: int = 10) -> List[TrendEvent]:
        return self._event_log[-n:]

    def get_events_for_topic(self, topic: str) -> List[TrendEvent]:
        return [e for e in self._event_log if e.topic == topic]

    def get_event_count(self) -> int:
        return len(self._event_log)

    def clear(self) -> None:
        self._event_log.clear()


class TrendEventEmitter:
    """Emits appropriate events based on trend analysis changes."""

    def __init__(self, event_bus: TrendEventBus) -> None:
        self._bus = event_bus
        self._previous_state: Dict[str, Dict] = {}

    def analyze_and_emit(self, topic: str, analysis: Any) -> None:
        """Analyze changes and emit events."""
        prev = self._previous_state.get(topic, {})
        events = []

        # Score change
        score = analysis.normalized.normalized_score if analysis.normalized else 0.0
        prev_score = prev.get("score", 0.0)

        if not prev:
            events.append(TrendEvent(TREND_DETECTED, topic, {"score": score}))
        elif score > 0:
            events.append(TrendEvent(TREND_UPDATED, topic, {
                "score": score, "previous_score": prev_score,
                "change": score - prev_score,
            }))

        # Lifecycle change
        lifecycle = analysis.lifecycle.stage if analysis.lifecycle else "unknown"
        prev_lifecycle = prev.get("lifecycle", "unknown")
        if lifecycle != prev_lifecycle and prev_lifecycle != "unknown":
            events.append(TrendEvent(TREND_LIFECYCLE_CHANGED, topic, {
                "from": prev_lifecycle, "to": lifecycle,
            }))
            if lifecycle == "dead":
                events.append(TrendEvent(TREND_EXPIRED, topic, {"lifecycle": lifecycle}))

        # Momentum change
        momentum = analysis.momentum.momentum_score if analysis.momentum else 0.0
        prev_momentum = prev.get("momentum", 0.0)
        if abs(momentum - prev_momentum) > 0.3:
            events.append(TrendEvent(TREND_MOMENTUM_CHANGED, topic, {
                "from": prev_momentum, "to": momentum,
            }))

        # Virality spike
        virality = analysis.virality.virality_score if analysis.virality else 0.0
        prev_virality = prev.get("virality", 0.0)
        if virality > 0.7 and prev_virality < 0.5:
            events.append(TrendEvent(TREND_VIRALITY_SPIKE, topic, {
                "virality_score": virality, "previous": prev_virality,
            }))

        # Low confidence
        confidence = analysis.confidence.overall_confidence if analysis.confidence else 0.0
        if confidence < 0.3:
            events.append(TrendEvent(TREND_CONFIDENCE_LOW, topic, {
                "confidence": confidence,
            }))

        # Prediction change
        if analysis.lifecycle and prev_lifecycle != "unknown":
            events.append(TrendEvent(TREND_PREDICTION_CHANGED, topic, {
                "lifecycle": lifecycle, "confidence": confidence,
            }))

        # Update state
        self._previous_state[topic] = {
            "score": score, "lifecycle": lifecycle,
            "momentum": momentum, "virality": virality,
        }

        # Emit all events
        for event in events:
            self._bus.publish(event)
