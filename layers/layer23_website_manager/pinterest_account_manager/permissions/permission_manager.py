"""PermissionManager — Manage posting, analytics, and API permissions per account."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_account_manager.models.pinterest_account import (
    PinterestAccount, AccountStatus,
)
from layers.layer23_website_manager.pinterest_account_manager.exceptions import PermissionDeniedError


class PermissionManager:
    """Granular permission management for each Pinterest account."""

    PERMISSION_TYPES = ["post", "analytics", "api", "boards", "admin"]

    def __init__(self) -> None:
        self._permission_log: List[dict] = []

    def check_permission(self, account: PinterestAccount, permission: str) -> bool:
        """Check if an account has a specific permission."""
        if permission == "post":
            return account.can_post and account.status == AccountStatus.ACTIVE
        elif permission == "analytics":
            return account.can_view_analytics
        elif permission == "api":
            return account.can_access_api
        elif permission == "boards":
            return account.can_manage_boards
        elif permission == "admin":
            return account.can_access_api and account.can_manage_boards
        return False

    def require_permission(self, account: PinterestAccount, permission: str) -> None:
        """Raise exception if permission is denied."""
        if not self.check_permission(account, permission):
            raise PermissionDeniedError(
                f"Account '{account.display_name}' lacks '{permission}' permission"
            )

    def set_permission(self, account: PinterestAccount, permission: str,
                        value: bool) -> bool:
        """Set a specific permission for an account."""
        if permission == "post":
            account.can_post = value
        elif permission == "analytics":
            account.can_view_analytics = value
        elif permission == "api":
            account.can_access_api = value
        elif permission == "boards":
            account.can_manage_boards = value
        else:
            setattr(account, f"can_{permission}", value)

        self._permission_log.append({
            "account_id": account.account_id,
            "permission": permission,
            "value": value,
            "timestamp": __import__("time").time(),
        })
        return True

    def get_permissions(self, account: PinterestAccount) -> Dict[str, bool]:
        """Get all permissions for an account."""
        return {
            "post": account.can_post,
            "analytics": account.can_view_analytics,
            "api": account.can_access_api,
            "boards": account.can_manage_boards,
            "healthy": account.is_healthy,
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "permission_changes": len(self._permission_log),
            "permission_types": self.PERMISSION_TYPES,
        }
