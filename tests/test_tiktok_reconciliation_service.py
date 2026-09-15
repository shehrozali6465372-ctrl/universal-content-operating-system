import tempfile
from pathlib import Path

import pytest

from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry, AccountSpec
from layers.layer07_publishing.modules.publisher_engine.content_repetition_guard import ContentRepetitionGuard
import layers.layer07_publishing.modules.publisher_engine.tiktok_reconciliation_service as service_module
from layers.layer07_publishing.modules.publisher_engine.tiktok_reconciliation_service import TikTokReconciliationService


class FakePublisher:
    def __init__(self):
        self.authenticated_with = None

    def authenticate(self, credentials):
        self.authenticated_with = credentials
        return True

    def get_post(self, tracking_id):
        return {"data": {"status": "PUBLISH_COMPLETE", "publicaly_available_post_id": ["public-42"]}}


def test_service_uses_registry_canonical_workspace_for_sanitized_account_ids(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        registry = AccountRegistry(str(root / "registry.sqlite3"), str(root / "workspaces"))
        account_id = "creator/a"
        registry.register(AccountSpec(account_id, "tiktok", "tech", credentials_ref="tt-a"))
        guard = ContentRepetitionGuard(str(registry.workspace_path(account_id) / "publishing_history.sqlite3"))
        decision = guard.reserve(account_id=account_id, platform="tiktok", content="Canonical workspace test.")
        guard.mark_pending(decision.reservation_id, "publish-42")

        publisher = FakePublisher()
        monkeypatch.setattr(service_module, "AccountCredentialResolver", type("Resolver", (), {"resolve": staticmethod(lambda ref: {"access_token": "account-token"})}))
        monkeypatch.setattr(service_module, "TikTokPublisher", lambda: publisher)

        result = TikTokReconciliationService(registry).reconcile(account_id)

        assert result[0]["published"] is True
        assert result[0]["post_id"] == "public-42"
        assert publisher.authenticated_with == {"access_token": "account-token"}
        assert ContentRepetitionGuard(str(registry.workspace_path(account_id) / "publishing_history.sqlite3")).pending(account_id) == []
        assert not (root / "workspaces" / account_id / "publishing_history.sqlite3").exists()


def test_service_rejects_unknown_disabled_and_wrong_platform_accounts():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        registry = AccountRegistry(str(root / "registry.sqlite3"), str(root / "workspaces"))
        registry.register(AccountSpec("ig-a", "instagram", "food"))
        registry.register(AccountSpec("tt-disabled", "tiktok", "tech", enabled=False))
        service = TikTokReconciliationService(registry)

        with pytest.raises(LookupError):
            service.reconcile("missing")
        with pytest.raises(ValueError, match="disabled"):
            service.reconcile("tt-disabled")
        with pytest.raises(ValueError, match="not tiktok"):
            service.reconcile("ig-a")
