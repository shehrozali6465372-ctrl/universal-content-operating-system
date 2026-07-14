"""
Global Event Bus
Cross-layer event-driven communication.

Usage:
    from layers.shared.event_bus import EventBus, EventType, Event

    bus = EventBus()
    bus.subscribe(EventType.POST_PUBLISHED, my_handler)
    bus.publish(Event(EventType.POST_PUBLISHED, source="layer07", data={"post_id": "123"}))
"""
from layers.shared.event_bus.event_bus import EventBus, EventHandler

__all__ = ["EventBus", "EventHandler"]
