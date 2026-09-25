"""Focused production-hardening regression tests for Layer 7."""

import time

from layers.layer07_publishing.modules.publisher_engine.publish_transaction import (
    PublishTransaction,
)
from layers.layer07_publishing.modules.failure_recovery.circuit_breaker import (
    CircuitBreaker,
    STATE_OPEN,
)


def test_publish_transaction_executes_callables_and_rolls_back_completed_steps():
    rolled_back = []
    txn = PublishTransaction("tx-prod-1")
    txn.add_step("prepare", lambda: True,
                  lambda: (rolled_back.append("prepare"), True)[1])
    txn.add_step("publish", lambda: False,
                  lambda: (rolled_back.append("publish"), True)[1])

    assert txn.execute() is False
    assert txn.is_completed is False
    assert txn.is_rolled_back is True
    assert rolled_back == ["prepare"]
    assert txn.get_steps()[1]["executed"] is False


def test_publish_transaction_is_single_use():
    txn = PublishTransaction("tx-prod-2")
    txn.add_step("publish", lambda: True)
    assert txn.execute() is True
    try:
        txn.execute()
    except RuntimeError:
        return
    raise AssertionError("transaction allowed a second execution")


def test_circuit_breaker_allows_only_one_half_open_probe():
    breaker = CircuitBreaker(
        failure_threshold=2,
        recovery_timeout=0.01,
        success_threshold=2,
    )
    breaker.record_failure("facebook")
    breaker.record_failure("facebook")
    assert breaker.get_state("facebook") == STATE_OPEN
    time.sleep(0.02)

    assert breaker.can_execute("facebook") is True
    assert breaker.can_execute("facebook") is False
    breaker.record_failure("facebook")
    assert breaker.get_state("facebook") == STATE_OPEN


def test_url_only_platform_does_not_send_local_media_paths():
    from layers.layer07_publishing.modules.publisher_engine.publish_request import PublishRequest
    from layers.layer07_publishing.modules.publisher_engine.publisher_manager import PublisherManager
    from layers.layer07_publishing.modules.media_manager.media_asset import MediaAsset
    from layers.layer07_publishing.modules.platform_plugin_manager.plugin_manager import PluginManager
    from tests.layer07_publishing.test_publisher_engine import MockPublisher

    registry = PluginManager()
    registry.register("instagram", MockPublisher)
    request = PublishRequest(platform="instagram", content="hello")
    request.media_assets = [MediaAsset("/local/image.png")]

    manager = PublisherManager(plugin_manager=registry)
    result = manager.publish(request)

    assert result.success is False
    assert result.error_category == "media"
    assert "public media URL" in result.error_message


def test_runtime_media_sanitizes_account_workspace(monkeypatch, tmp_path):
    from layers.layer07_publishing.modules.media_manager.runtime_media import RuntimeMedia

    monkeypatch.setenv("UCOS_ACCOUNT_WORKSPACES", str(tmp_path))
    monkeypatch.setenv("UCOS_PUBLIC_MEDIA_BASE_URL", "https://media.example.test")
    path = tmp_path / "safe" / "image.png"
    path.parent.mkdir()
    path.write_bytes(b"data")

    url = RuntimeMedia.public_url(str(path))
    assert url == "https://media.example.test/safe/image.png"

    safe = RuntimeMedia._safe_account_id("../../escape")
    assert "/" not in safe
    assert "\\" not in safe
