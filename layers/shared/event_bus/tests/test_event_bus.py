import threading

from layers.shared.event_bus.event_bus import EventBus
from layers.shared.models.event import Event, EventType


def make_event():
    return Event(event_type=EventType.AGENT_STARTED, data={"ok": True})


def test_duplicate_subscription_is_rejected():
    bus = EventBus()
    calls = []
    callback = lambda event: calls.append(event)
    assert bus.subscribe(EventType.AGENT_STARTED, callback) is True
    assert bus.subscribe(EventType.AGENT_STARTED, callback) is False
    assert bus.get_handler_count(EventType.AGENT_STARTED) == 1


def test_once_and_wildcard_handlers_are_removed_after_dispatch():
    bus = EventBus()
    calls = []
    bus.subscribe(EventType.AGENT_STARTED, lambda event: calls.append("specific"), once=True)
    bus.subscribe_all(lambda event: calls.append("wildcard"), once=False)
    result = bus.publish(make_event())
    assert result["handlers_notified"] == 2
    assert calls == ["specific", "wildcard"]
    assert bus.get_handler_count(EventType.AGENT_STARTED) == 0
    assert bus.get_handler_count() == 1


def test_callback_failure_is_isolated_and_counted():
    bus = EventBus()
    bus.subscribe(EventType.AGENT_STARTED, lambda event: (_ for _ in ()).throw(ValueError("boom")))
    result = bus.publish(make_event())
    assert len(result["errors"]) == 1
    assert bus.get_stats()["total_errors"] == 1


def test_concurrent_publish_and_unsubscribe_are_safe():
    bus = EventBus()
    lock = threading.Lock()
    calls = {"count": 0}

    def callback(event):
        with lock:
            calls["count"] += 1

    bus.subscribe(EventType.AGENT_STARTED, callback)
    threads = [
        threading.Thread(target=lambda: [bus.publish(make_event()) for _ in range(50)])
        for _ in range(4)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert bus.get_stats()["total_publishes"] == 200
    assert calls["count"] == 200


def test_history_limit_and_clear_are_synchronized():
    bus = EventBus(max_history=2)
    bus.publish(make_event())
    bus.publish(make_event())
    bus.publish(make_event())
    assert len(bus.get_history()) == 2
    bus.clear_history()
    assert bus.get_history() == []
