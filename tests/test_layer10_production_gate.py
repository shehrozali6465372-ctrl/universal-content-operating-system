"""Layer 10 production certification gate.

These tests focus on invariants that ordinary feature tests can miss:
bounded state, honest execution semantics, and concurrency-safe request handling.
"""
from concurrent.futures import ThreadPoolExecutor

from layers.layer10_monetization.modules.universal_os.api_gateway import APIGateway
from layers.layer10_monetization.modules.universal_os.authentication_manager import (
    AuthenticationManager,
)
from layers.layer10_monetization.modules.universal_os.distributed_executor import (
    DistributedExecutor,
)
from layers.layer10_monetization.modules.universal_os.event_stream import EventStream
from layers.layer10_monetization.modules.universal_os.global_memory import GlobalMemory
from layers.layer10_monetization.modules.universal_os.universal_ai_os import (
    SystemState,
    UniversalAIOS,
)


def test_api_gateway_history_and_client_state_are_bounded() -> None:
    gateway = APIGateway(rate_limit=100, max_history=25, max_clients=10)
    gateway.register_handler("health", lambda request: {"ok": True})

    for index in range(100):
        gateway.handle("health", client_id=f"client-{index % 10}")

    stats = gateway.get_stats()
    assert stats["retained_requests"] <= 25
    assert stats["tracked_clients"] <= 10


def test_api_gateway_handles_concurrent_requests_without_corrupting_state() -> None:
    gateway = APIGateway(rate_limit=1000, max_history=1000)
    gateway.register_handler("health", lambda request: {"ok": True})

    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = list(
            pool.map(
                lambda index: gateway.handle("health", client_id=f"c-{index % 8}"),
                range(200),
            )
        )

    assert all(response.status_code == 200 for response in responses)
    assert gateway.get_stats()["total_requests"] == 200


def test_authentication_state_is_bounded() -> None:
    auth = AuthenticationManager(max_records=5)
    for index in range(20):
        auth.create_token(f"user-{index}")
        auth.create_api_key(f"app-{index}")
        auth.create_session(f"user-{index}")

    stats = auth.get_stats()
    assert stats["total_tokens"] <= 5
    assert stats["api_keys"] <= 5
    assert stats["sessions"] <= 5


def test_executor_never_fabricates_success_for_missing_callable() -> None:
    executor = DistributedExecutor()
    task = executor.submit("unconfigured")
    result = executor.execute_next()

    assert result is task
    assert task.status == "failed"
    assert task.error == "NoExecutableFunction"
    assert executor.get_completed() == []
    assert executor.get_failed() == [task]


def test_event_stream_retention_is_bounded() -> None:
    stream = EventStream(max_events=10)
    for index in range(100):
        stream.publish(f"event-{index}")

    assert stream.get_stats()["total_events"] == 10
    assert len(stream.get_events(count=100)) == 10


def test_global_memory_eviction_keeps_index_consistent() -> None:
    memory = GlobalMemory(max_entries=3)
    for index in range(5):
        memory.store("business", f"k-{index}", index)

    assert memory.retrieve("business", "k-0") is None
    assert memory.retrieve("business", "k-4") == 4
    assert memory.get_stats()["total"] == 3


def test_universal_ai_os_rejects_transitional_reentry_and_bounds_events() -> None:
    os = UniversalAIOS()
    assert os.start() is True
    os._state = SystemState.STARTING
    assert os.start() is False

    os._state = SystemState.RUNNING
    for _ in range(11000):
        os._record_event("probe")

    assert len(os._events) == 10000
    assert os.status()["state"] == SystemState.RUNNING
