"""Account-aware TikTok reconciliation entrypoint."""
from __future__ import annotations
import os
from pathlib import Path
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
        accounts = [self.registry.get(account_id)] if account_id else self.registry.list(platform="tiktok", enabled_only=True)
        outcomes: list[Dict[str, Any]] = []
        root = Path(os.environ.get("UCOS_ACCOUNT_WORKSPACES", "./data/accounts/workspaces"))
        for account in accounts:
            if account is None or account.platform != "tiktok" or not account.enabled:
                continue
            credentials = AccountCredentialResolver.resolve(account.credentials_ref)
            publisher = TikTokPublisher()
            if not credentials or not publisher.authenticate(credentials):
                outcomes.append({"account_id": account.account_id, "status": "UNCONFIGURED", "reconciled": 0})
                continue
            guard = ContentRepetitionGuard(str(root / account.account_id / "publishing_history.sqlite3"))
            results = TikTokReconciliation(guard).reconcile(publisher, account_id=account.account_id)
            outcomes.extend(results or [{"account_id": account.account_id, "status": "NO_PENDING", "reconciled": 0}])
        return outcomes
