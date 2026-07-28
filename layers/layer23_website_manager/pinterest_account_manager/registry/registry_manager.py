"""RegistryManager — Pinterest account CRUD operations."""
from __future__ import annotations
import time
import json
import threading
import os
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_account_manager.models.pinterest_account import (
    PinterestAccount, AccountStatus, AuthStatus,
)
from layers.layer23_website_manager.pinterest_account_manager.exceptions import (
    AccountNotFoundError, DuplicateAccountError, AccountLimitError,
)


class RegistryManager:
    """Register, update, remove, enable/disable, archive Pinterest accounts."""

    def __init__(self, max_accounts: int = 61, storage_dir: str = "") -> None:
        self._accounts: Dict[str, PinterestAccount] = {}
        self._lock = threading.Lock()
        self._max_accounts = max_accounts
        self._storage_dir = storage_dir
        self._total_registrations = 0

        # Load from disk
        if storage_dir:
            self._load_from_disk()

    # ─── CRUD ──────────────────────────────────────────────

    def register(self, account_name: str, username: str = "",
                  niche: str = "", business_name: str = "",
                  website: str = "", access_token: str = "",
                  refresh_token: str = "", description: str = "") -> PinterestAccount:
        """Register a new Pinterest Business Account."""
        if len(self._accounts) >= self._max_accounts:
            raise AccountLimitError(f"Account limit reached: {self._max_accounts}")

        # Check for duplicates
        normalized = (account_name or username).lower().strip()
        for acc in self._accounts.values():
            existing = (acc.account_name or acc.username).lower().strip()
            if existing == normalized:
                raise DuplicateAccountError(f"Account '{account_name}' already exists")

        account = PinterestAccount(
            account_name=account_name,
            username=username or account_name.lower().replace(" ", "_"),
            niche=niche,
            business_name=business_name,
            website=website,
            description=description,
            access_token=access_token,
            refresh_token=refresh_token,
        )

        if access_token:
            account.auth_status = AuthStatus.AUTHENTICATED

        with self._lock:
            self._accounts[account.account_id] = account
            self._total_registrations += 1

        return account

    def get(self, account_id: str) -> Optional[PinterestAccount]:
        """Get account by ID."""
        return self._accounts.get(account_id)

    def get_by_name(self, account_name: str) -> Optional[PinterestAccount]:
        """Find account by name (case-insensitive)."""
        for acc in self._accounts.values():
            if acc.account_name.lower() == account_name.lower():
                return acc
        return None

    def update(self, account_id: str, **kwargs) -> Optional[PinterestAccount]:
        """Update account fields. Returns updated account or None."""
        account = self._accounts.get(account_id)
        if not account:
            return None

        allowed = {
            "account_name", "username", "niche", "business_name",
            "profile_image", "banner", "description", "website",
            "contact_email", "contact_phone", "notes",
            "brand_colors", "brand_logo", "brand_banner", "voice_profile",
            "can_post", "can_view_analytics", "can_access_api", "can_manage_boards",
            "follower_count", "monthly_views", "engagement_rate",
        }

        with self._lock:
            for key, value in kwargs.items():
                if key in allowed:
                    setattr(account, key, value)
            account.updated_at = time.time()

        return account

    def remove(self, account_id: str) -> bool:
        """Permanently remove an account."""
        with self._lock:
            return self._accounts.pop(account_id, None) is not None

    def set_status(self, account_id: str, status: AccountStatus) -> bool:
        """Set account status (active, disabled, archived, etc.)."""
        account = self._accounts.get(account_id)
        if not account:
            return False
        with self._lock:
            account.status = status
            account.updated_at = time.time()
        return True

    def enable(self, account_id: str) -> bool:
        return self.set_status(account_id, AccountStatus.ACTIVE)

    def disable(self, account_id: str) -> bool:
        return self.set_status(account_id, AccountStatus.DISABLED)

    def archive(self, account_id: str) -> bool:
        return self.set_status(account_id, AccountStatus.MAINTENANCE)

    # ─── Queries ───────────────────────────────────────────

    def get_all(self, status: Optional[AccountStatus] = None,
                 niche: str = "", healthy_only: bool = False) -> List[PinterestAccount]:
        """Get all accounts, optionally filtered."""
        accounts = list(self._accounts.values())

        if status:
            accounts = [a for a in accounts if a.status == status]
        if niche:
            accounts = [a for a in accounts if a.niche.lower() == niche.lower()]
        if healthy_only:
            accounts = [a for a in accounts if a.is_healthy]

        return sorted(accounts, key=lambda a: (a.status.value, a.health_score), reverse=True)

    def count(self) -> int:
        return len(self._accounts)

    def get_by_niche(self, niche: str) -> List[PinterestAccount]:
        return self.get_all(niche=niche)

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        by_status: Dict[str, int] = {}
        by_niche: Dict[str, int] = {}
        healthy = 0

        for acc in self._accounts.values():
            s = acc.status.value
            by_status[s] = by_status.get(s, 0) + 1
            n = acc.niche or "uncategorized"
            by_niche[n] = by_niche.get(n, 0) + 1
            if acc.is_healthy:
                healthy += 1

        return {
            "total_accounts": len(self._accounts),
            "max_accounts": self._max_accounts,
            "available_slots": self._max_accounts - len(self._accounts),
            "by_status": by_status,
            "by_niche": by_niche,
            "healthy_count": healthy,
            "unhealthy_count": len(self._accounts) - healthy,
            "total_registrations": self._total_registrations,
        }

    def _load_from_disk(self) -> None:
        path = os.path.join(self._storage_dir, "pinterest_accounts.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                for item in data:
                    acc = PinterestAccount(**item)
                    self._accounts[acc.account_id] = acc
            except Exception:
                pass

    def save_to_disk(self) -> None:
        if not self._storage_dir:
            return
        os.makedirs(self._storage_dir, exist_ok=True)
        path = os.path.join(self._storage_dir, "pinterest_accounts.json")
        with open(path, "w") as f:
            json.dump([a.to_dict() for a in self._accounts.values()], f, indent=2)
