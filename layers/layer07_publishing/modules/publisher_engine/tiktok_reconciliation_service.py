"""Account-aware TikTok reconciliation entrypoint."""
from __future__ import annotations
from typing import Any, Dict, Optional

from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
from layers.layer07_publishing.modules.account_control.credential_resolver import AccountCredentialResolver
from layers.layer07_publishing.modules.platform_plugin_manager.tiktok.tiktok_publisher import TikTokPublisher
from .content_repetition_guard import ContentRepetitionGuard
from .tiktok_reconciliation import TikTokReconciliation


class TikTokReconciliationService:
    """Reconcile pending TikTok submissions using only each account's credentials."""

    def __init__(self, registry: Optional[AccountRegistry] = None) -> None:
        self.registry = registry or AccountRegistry()

    def reconcile(self, account_id: Optional[str] = None) -> list[Dict[str, Any]]:
        if account_id:
            account = self.registry.get(account_id)
            if account is None:
                raise LookupError(f"unknown account_id: {account_id}")
            if not account.enabled:
                raise ValueError(f"disabled account_id: {account_id}")
            if account.platform != "tiktok":
                raise ValueError(f"account {account_id} belongs to {account.platform}, not tiktok")
            accounts = [account]
        else:
            accounts = self.registry.list(platform="tiktok", enabled_only=True)

        outcomes: list[Dict[str, Any]] = []
        for account in accounts:
            credentials = AccountCredentialResolver.resolve(account.credentials_ref)
            publisher = TikTokPublisher()
            if not credentials or not publisher.authenticate(credentials):
                outcomes.append({"account_id": account.account_id, "status": "UNCONFIGURED", "reconciled": 0})
                continue
            # Always use the registry's canonical workspace path so sanitized or
            # hashed account IDs cannot escape or collide with another account.
            history_path = self.registry.workspace_path(account.account_id) / "publishing_history.sqlite3"
            guard = ContentRepetitionGuard(str(history_path))
            results = TikTokReconciliation(guard).reconcile(publisher, account_id=account.account_id)
            outcomes.extend(results or [{"account_id": account.account_id, "status": "NO_PENDING", "reconciled": 0}])
        return outcomes
