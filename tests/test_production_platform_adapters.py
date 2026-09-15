import json

from layers.layer07_publishing.modules.platform_plugin_manager.plugin_manager import PluginManager
from layers.layer07_publishing.modules.platform_plugin_manager.tiktok.tiktok_publisher import TikTokPublisher
from layers.layer07_publishing.modules.publisher_engine.content_repetition_guard import ContentRepetitionGuard


def test_target_platform_adapters_are_registered():
    manager = PluginManager()
    platforms = set(manager.registry.list_platforms())
    assert {"facebook", "instagram", "pinterest", "youtube", "tiktok"}.issubset(platforms)


def test_unconfigured_real_adapters_do_not_claim_authentication():
    manager = PluginManager()
    for platform in ("pinterest", "youtube", "tiktok"):
        publisher = manager.registry.get_instance(platform)
        assert publisher is not None
        assert publisher.authenticate({}) is False


def test_capabilities_are_platform_specific():
    manager = PluginManager()
    assert manager.get_capabilities("youtube").supports_video
    assert manager.get_capabilities("tiktok").supports_video
    assert manager.get_capabilities("pinterest").supports_images
    assert manager.get_capabilities("instagram").supports_video


def test_tiktok_publish_id_is_pending_not_final_post_id(monkeypatch):
    publisher = TikTokPublisher()
    publisher.token = "token"
    publisher.authenticated = True
    publisher._post = lambda path, body: {"data": {"publish_id": "publish-123"}}
    result = publisher.publish("hello", ["https://cdn.example/media.mp4"], "video")
    assert result.success is False
    assert result.post_id == ""
    assert result.metadata["publish_state"] == "processing"
    assert result.metadata["tracking_id"] == "publish-123"


def test_pending_repetition_reservation_blocks_duplicate_until_resolved(tmp_path):
    guard = ContentRepetitionGuard(str(tmp_path / "history.sqlite3"))
    first = guard.reserve(account_id="acct-a", platform="tiktok", content="A unique post structure.")
    assert first.allowed
    guard.mark_pending(first.reservation_id, "publish-123")
    duplicate = guard.reserve(account_id="acct-a", platform="tiktok", content="A unique post structure.")
    assert duplicate.allowed is False
    assert duplicate.reason == "exact_content_repeat"
    guard.finalize(first.reservation_id, "final-post-456")
    assert guard.reserve(account_id="acct-a", platform="tiktok", content="A unique post structure.").allowed is False
