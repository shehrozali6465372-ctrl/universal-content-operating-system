"""PinterestAccountManager — Universal AI Content Operating System Layer 23 / Module 2.

Centrally manages all Pinterest Business Accounts — registration, authentication,
branding, health monitoring, and AI-powered account selection.

Version: 1.0.0
"""
from __future__ import annotations
import time
import os
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_account_manager.models.pinterest_account import (
    PinterestAccount, AccountStatus, AuthStatus,
)
from layers.layer23_website_manager.pinterest_account_manager.models.account_token import AccountToken
from layers.layer23_website_manager.pinterest_account_manager.models.brand_profile import BrandProfile
from layers.layer23_website_manager.pinterest_account_manager.registry.registry_manager import RegistryManager
from layers.layer23_website_manager.pinterest_account_manager.auth.oauth_manager import OAuthManager
from layers.layer23_website_manager.pinterest_account_manager.permissions.permission_manager import PermissionManager
from layers.layer23_website_manager.pinterest_account_manager.branding.branding_manager import BrandingManager
from layers.layer23_website_manager.pinterest_account_manager.services.website_claim_manager import WebsiteClaimManager
from layers.layer23_website_manager.pinterest_account_manager.health.account_health import AccountHealthChecker
from layers.layer23_website_manager.pinterest_account_manager.selector.account_selector import AccountSelector
from layers.layer23_website_manager.pinterest_account_manager.exceptions import (
    AccountNotFoundError, SelectionError, AccountSuspendedError,
)


class PinterestAccountManager:
    """Primary facade for Pinterest Account Management Platform.

    Coordinates: registry, auth, permissions, branding, website claims,
    health monitoring, and AI-powered account selection.
    """

    def __init__(self, max_accounts: int = 61, storage_dir: str = "") -> None:
        self._lock = threading.RLock()
        self._start_time = time.time()

        # Sub-modules
        self.registry = RegistryManager(max_accounts=max_accounts, storage_dir=storage_dir)
        self.auth = OAuthManager()
        self.permissions = PermissionManager()
        self.branding = BrandingManager()
        self.claims = WebsiteClaimManager()
        self.health = AccountHealthChecker()
        self.selector = AccountSelector()

        # Stats
        self._total_operations = 0
        self._operation_log: List[dict] = []

    # ─── Account Lifecycle ────────────────────────────────

    def register_account(self, account_name: str, username: str = "",
                          niche: str = "", business_name: str = "",
                          website: str = "", access_token: str = "",
                          refresh_token: str = "", description: str = "") -> PinterestAccount:
        """Register new Pinterest account."""
        account = self.registry.register(
            account_name=account_name,
            username=username,
            niche=niche,
            business_name=business_name,
            website=website,
            access_token=access_token,
            refresh_token=refresh_token,
            description=description,
        )

        # Register token if provided
        if access_token:
            self.auth.register_token(
                account_id=account.account_id,
                access_token=access_token,
                refresh_token=refresh_token,
            )

        # Create brand profile from niche
        if niche:
            self.branding.create_from_niche(account.account_id, niche)

        # Initiate website claim
        if website:
            self.claims.claim_website(account.account_id, website)

        self._log_operation("register_account", {"account_name": account_name, "niche": niche})
        return account

    def get_account(self, account_id: str) -> Optional[PinterestAccount]:
        return self.registry.get(account_id)

    def update_account(self, account_id: str, **kwargs) -> Optional[PinterestAccount]:
        result = self.registry.update(account_id, **kwargs)
        if result:
            self._log_operation("update_account", {"account_id": account_id})
        return result

    def remove_account(self, account_id: str) -> bool:
        """Remove account and all associated data."""
        self.auth.remove_token(account_id)
        self.claims.remove_claim(account_id)
        result = self.registry.remove(account_id)
        if result:
            self._log_operation("remove_account", {"account_id": account_id})
        return result

    def enable_account(self, account_id: str) -> bool:
        return self.registry.enable(account_id)

    def disable_account(self, account_id: str) -> bool:
        return self.registry.disable(account_id)

    def archive_account(self, account_id: str) -> bool:
        return self.registry.archive(account_id)

    # ─── Authentication ───────────────────────────────────

    def set_token(self, account_id: str, access_token: str,
                   refresh_token: str = "", expires_in: int = 3600 * 24 * 30) -> AccountToken:
        """Set OAuth token for an account."""
        token = self.auth.register_token(account_id, access_token, refresh_token, expires_in=expires_in)
        account = self.registry.get(account_id)
        if account:
            account.access_token = access_token
            account.refresh_token = refresh_token
            account.token_expiry = token.expiry_time
            account.auth_status = AuthStatus.AUTHENTICATED
            account.updated_at = time.time()
        self._log_operation("set_token", {"account_id": account_id})
        return token

    def refresh_token(self, account_id: str) -> Optional[AccountToken]:
        """Refresh OAuth token."""
        token = self.auth.refresh_token(account_id)
        if token:
            account = self.registry.get(account_id)
            if account:
                account.token_expiry = token.expiry_time
                account.auth_status = AuthStatus.AUTHENTICATED
                account.updated_at = time.time()
            self._log_operation("refresh_token", {"account_id": account_id})
        return token

    def validate_auth(self, account_id: str) -> tuple:
        """Validate authentication for an account."""
        return self.auth.validate_token(account_id)

    # ─── Account Selection ────────────────────────────────

    def select_account(self, topic: str, niche: str = "") -> PinterestAccount:
        """AI-powered account selection — best account for a topic."""
        accounts = self.registry.get_all(healthy_only=True)
        if not accounts:
            accounts = self.registry.get_all()
        if not accounts:
            raise SelectionError("No Pinterest accounts registered")

        account = self.selector.select(topic, accounts, niche=niche)
        self._log_operation("select_account", {"topic": topic, "selected": account.account_name})
        return account

    def select_accounts_for_topics(self, topics: List[str]) -> Dict[str, PinterestAccount]:
        """Select accounts for multiple topics."""
        accounts = self.registry.get_all(healthy_only=True)
        if not accounts:
            accounts = self.registry.get_all()
        return self.selector.select_multi(topics, accounts)

    # ─── Health ───────────────────────────────────────────

    def check_health(self, account_id: str) -> Dict[str, Any]:
        """Check health of a single account."""
        account = self.registry.get(account_id)
        if not account:
            return {"error": "Account not found"}

        is_valid, _ = self.auth.validate_token(account_id)
        result = self.health.check_account(account, has_valid_token=is_valid)

        # Update account health
        account.health_score = result["health_score"]
        account.health_issues = result["issues"]
        account.last_health_check = time.time()

        return result

    def check_all_health(self) -> Dict[str, Any]:
        """Check health of all accounts."""
        accounts = self.registry.get_all()
        token_status = {}
        for acc in accounts:
            is_valid, _ = self.auth.validate_token(acc.account_id)
            token_status[acc.account_id] = is_valid
        return self.health.check_all(accounts, token_status)

    # ─── Branding ─────────────────────────────────────────

    def create_brand_profile(self, account_id: str, brand_name: str,
                               brand_voice: str = "professional",
                               brand_colors: Optional[Dict[str, str]] = None) -> BrandProfile:
        return self.branding.create_profile(account_id, brand_name, brand_voice, brand_colors)

    def get_brand_profile(self, account_id: str) -> Optional[BrandProfile]:
        return self.branding.get_profile(account_id)

    def sync_branding(self, account_id: str) -> Dict[str, Any]:
        result = self.branding.sync_branding(account_id)
        self._log_operation("sync_branding", {"account_id": account_id})
        return result

    # ─── Website Claims ───────────────────────────────────

    def claim_website(self, account_id: str, website: str) -> dict:
        """Claim a website for a Pinterest account."""
        result = self.claims.claim_website(account_id, website)
        account = self.registry.get(account_id)
        if account:
            account.website = website
            account.website_claimed = False
            account.claim_status = "pending"
            account.updated_at = time.time()
        self._log_operation("claim_website", {"account_id": account_id, "website": website})
        return result

    def verify_website_claim(self, account_id: str) -> dict:
        """Verify website claim."""
        result = self.claims.verify_claim(account_id)
        account = self.registry.get(account_id)
        if account:
            account.website_claimed = True
            account.claim_status = "verified"
            account.updated_at = time.time()
        self._log_operation("verify_website_claim", {"account_id": account_id})
        return result

    # ─── Permissions ─────────────────────────────────────

    def check_permission(self, account_id: str, permission: str) -> bool:
        account = self.registry.get(account_id)
        if not account:
            return False
        return self.permissions.check_permission(account, permission)

    def set_permission(self, account_id: str, permission: str, value: bool) -> bool:
        account = self.registry.get(account_id)
        if not account:
            return False
        self.permissions.set_permission(account, permission, value)
        return True

    # ─── Status & Stats ──────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive Pinterest Account Manager status."""
        registry_stats = self.registry.get_stats()
        health_report = self.check_all_health()
        auth_summary = self.auth.check_expiry_all()

        return {
            "module": "Pinterest Account Manager (Layer 23 / Module 2)",
            "version": "1.0.0",
            "overall": "Healthy" if health_report["overall_score"] >= 70 else "Degraded",
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "accounts": {
                "total": registry_stats["total_accounts"],
                "max": registry_stats["max_accounts"],
                "available_slots": registry_stats["available_slots"],
                "healthy": registry_stats["healthy_count"],
                "unhealthy": registry_stats["unhealthy_count"],
                "by_status": registry_stats["by_status"],
                "by_niche": registry_stats["by_niche"],
            },
            "health": {
                "overall_score": health_report["overall_score"],
                "healthy": health_report["healthy"],
                "degraded": health_report["degraded"],
                "critical": health_report["critical"],
            },
            "authentication": {
                "tokens": auth_summary["total"],
                "healthy": auth_summary["healthy"],
                "expiring_soon": auth_summary["expiring_soon"],
                "expired": auth_summary["expired"],
            },
            "operations": {
                "total": self._total_operations,
            },
        }

    def to_dict(self) -> Dict[str, Any]:
        return self.get_status()

    # ─── Internal ─────────────────────────────────────────

    def _log_operation(self, operation: str, details: dict) -> None:
        with self._lock:
            self._total_operations += 1
            self._operation_log.append({
                "operation": operation,
                "details": details,
                "timestamp": time.time(),
            })

    def get_operation_log(self, limit: int = 50) -> List[dict]:
        return self._operation_log[-limit:]


# ─── Singleton Access ───────────────────────────────────────────────────────

_pinterest_manager_instance: Optional[PinterestAccountManager] = None
_instance_lock = threading.Lock()


def get_pinterest_manager(max_accounts: int = 61) -> PinterestAccountManager:
    """Get or create the singleton PinterestAccountManager."""
    global _pinterest_manager_instance
    if _pinterest_manager_instance is None:
        with _instance_lock:
            if _pinterest_manager_instance is None:
                storage = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "pinterest")
                _pinterest_manager_instance = PinterestAccountManager(
                    max_accounts=max_accounts,
                    storage_dir=storage,
                )
    return _pinterest_manager_instance
