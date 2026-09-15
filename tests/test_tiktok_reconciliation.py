import tempfile
from pathlib import Path

from layers.layer07_publishing.modules.publisher_engine.content_repetition_guard import ContentRepetitionGuard
from layers.layer07_publishing.modules.publisher_engine.tiktok_reconciliation import TikTokReconciliation


class FakeTikTok:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get_post(self, tracking_id):
        self.calls.append(tracking_id)
        return self.payload


def _pending(tmp_path):
    guard = ContentRepetitionGuard(str(tmp_path / "history.sqlite3"))
    decision = guard.reserve(account_id="tt-a", platform="tiktok", content="Unique async post.")
    guard.mark_pending(decision.reservation_id, "publish-123")
    return guard, decision.reservation_id


def test_tiktok_reconciliation_finalizes_only_real_public_post_id(tmp_path):
    guard, reservation_id = _pending(tmp_path)
    publisher = FakeTikTok({"data": {"status": "PUBLISH_COMPLETE", "publicaly_available_post_id": [987654]}})

    result = TikTokReconciliation(guard).reconcile(publisher, account_id="tt-a")

    assert result[0]["published"] is True
    assert result[0]["post_id"] == "987654"
    assert guard.pending("tt-a") == []


def test_tiktok_reconciliation_keeps_pending_without_public_post_id(tmp_path):
    guard, _ = _pending(tmp_path)
    publisher = FakeTikTok({"data": {"status": "PUBLISH_COMPLETE", "publicaly_available_post_id": []}})

    result = TikTokReconciliation(guard).reconcile(publisher, account_id="tt-a")

    assert result[0]["published"] is False
    assert result[0]["reason"] == "awaiting_final_public_post_id"
    assert len(guard.pending("tt-a")) == 1


def test_tiktok_reconciliation_releases_failed_submission(tmp_path):
    guard, _ = _pending(tmp_path)
    publisher = FakeTikTok({"data": {"status": "FAILED", "fail_reason": "video_pull_failed"}})

    result = TikTokReconciliation(guard).reconcile(publisher, account_id="tt-a")

    assert result[0]["released"] is True
    assert result[0]["published"] if "published" in result[0] else True
    assert guard.pending("tt-a") == []


def test_tiktok_reconciliation_keeps_pending_on_api_error(tmp_path):
    guard, _ = _pending(tmp_path)

    class Broken:
        def get_post(self, tracking_id):
            raise RuntimeError("temporary network failure")

    result = TikTokReconciliation(guard).reconcile(Broken(), account_id="tt-a")

    assert result[0]["status"] == "UNKNOWN"
    assert result[0]["released"] is False
    assert len(guard.pending("tt-a")) == 1
