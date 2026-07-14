"""Tests for EventBus."""

from layers.shared.event_bus import EventBus
from layers.shared.models.event import Event, EventType


class TestEventBus:
    def setup_method(self):
        self.bus = EventBus()

    def test_subscribe_and_publish(self):
        received = []
        self.bus.subscribe(EventType.POST_PUBLISHED, lambda e: received.append(e))
        event = Event(EventType.POST_PUBLISHED, data={"post_id": "1"})
        self.bus.publish(event)
        assert len(received) == 1
        assert received[0].data["post_id"] == "1"

    def test_multiple_handlers(self):
        results = {"a": 0, "b": 0}
        self.bus.subscribe(EventType.POST_PUBLISHED, lambda e: results.update({"a": 1}))
        self.bus.subscribe(EventType.POST_PUBLISHED, lambda e: results.update({"b": 1}))
        self.bus.publish(Event(EventType.POST_PUBLISHED))
        assert results["a"] == 1
        assert results["b"] == 1

    def test_unsubscribe(self):
        self.bus.subscribe(EventType.POST_PUBLISHED, lambda e: None, name="handler1")
        assert self.bus.unsubscribe(EventType.POST_PUBLISHED, "handler1") is True
        assert self.bus.get_handler_count(EventType.POST_PUBLISHED) == 0

    def test_unsubscribe_nonexistent(self):
        assert self.bus.unsubscribe(EventType.POST_PUBLISHED, "nope") is False

    def test_once_handler(self):
        count = [0]
        self.bus.subscribe(EventType.POST_PUBLISHED, lambda e: count.__setitem__(0, count[0] + 1), once=True)
        self.bus.publish(Event(EventType.POST_PUBLISHED))
        self.bus.publish(Event(EventType.POST_PUBLISHED))
        assert count[0] == 1

    def test_priority_order(self):
        order = []
        self.bus.subscribe(EventType.POST_PUBLISHED, lambda e: order.append("low"), priority=1)
        self.bus.subscribe(EventType.POST_PUBLISHED, lambda e: order.append("high"), priority=10)
        self.bus.publish(Event(EventType.POST_PUBLISHED))
        assert order == ["high", "low"]

    def test_wildcard_subscription(self):
        received = []
        self.bus.subscribe("*", lambda e: received.append(e))
        self.bus.publish(Event(EventType.POST_PUBLISHED))
        self.bus.publish(Event(EventType.TOPIC_DISCOVERED))
        assert len(received) == 2

    def test_publish_result(self):
        self.bus.subscribe(EventType.POST_PUBLISHED, lambda e: None)
        result = self.bus.publish(Event(EventType.POST_PUBLISHED))
        assert result["handlers_notified"] == 1
        assert result["errors"] == []

    def test_handler_error_isolation(self):
        def bad_handler(e):
            raise ValueError("oops")

        good_received = []
        self.bus.subscribe(EventType.POST_PUBLISHED, bad_handler, name="bad")
        self.bus.subscribe(EventType.POST_PUBLISHED, lambda e: good_received.append(1), name="good")
        result = self.bus.publish(Event(EventType.POST_PUBLISHED))
        assert len(result["errors"]) == 1
        assert len(good_received) == 1

    def test_subscribe_all(self):
        self.bus.subscribe_all(
            [EventType.POST_PUBLISHED, EventType.POST_FAILED],
            lambda e: None,
            name="multi",
        )
        assert self.bus.get_handler_count(EventType.POST_PUBLISHED) == 1
        assert self.bus.get_handler_count(EventType.POST_FAILED) == 1

    def test_history(self):
        self.bus.publish(Event(EventType.POST_PUBLISHED))
        self.bus.publish(Event(EventType.TOPIC_DISCOVERED))
        history = self.bus.get_history()
        assert len(history) == 2

    def test_history_filtered(self):
        self.bus.publish(Event(EventType.POST_PUBLISHED))
        self.bus.publish(Event(EventType.TOPIC_DISCOVERED))
        history = self.bus.get_history(event_type=EventType.POST_PUBLISHED)
        assert len(history) == 1

    def test_history_limit(self):
        for _ in range(10):
            self.bus.publish(Event(EventType.POST_PUBLISHED))
        history = self.bus.get_history(limit=3)
        assert len(history) == 3

    def test_get_stats(self):
        self.bus.subscribe(EventType.POST_PUBLISHED, lambda e: None)
        self.bus.publish(Event(EventType.POST_PUBLISHED))
        stats = self.bus.get_stats()
        assert stats["total_handlers"] == 1
        assert stats["total_publishes"] == 1

    def test_clear_history(self):
        self.bus.publish(Event(EventType.POST_PUBLISHED))
        self.bus.clear_history()
        assert len(self.bus.get_history()) == 0

    def test_reset(self):
        self.bus.subscribe(EventType.POST_PUBLISHED, lambda e: None)
        self.bus.publish(Event(EventType.POST_PUBLISHED))
        self.bus.reset()
        assert self.bus.get_handler_count() == 0
        assert self.bus.get_stats()["total_publishes"] == 0
