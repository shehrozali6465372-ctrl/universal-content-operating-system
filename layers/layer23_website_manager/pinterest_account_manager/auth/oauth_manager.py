"""OAuthManager — Pinterest OAuth token lifecycle management."""
from __future__ import annotations
import time
import json
import threading
from typing import Any, Dict, Optional, Tuple
from layers.layer23_website_manager.pinterest_account_manager.models.account_token import AccountToken
from layers.layer23_website_manager.pinterest_account_manager.models.pinterest_account import AuthStatus
from layers.layer23_website_manager.pinterest_account_manager.exceptions import (
    InvalidTokenError, TokenExpiredError,
)


class OAuthManager:
    """Manage OAuth 2.0 tokens — refresh, validate, expiry tracking."""

    def __init__(self) -> None:
        self._tokens: Dict[str, AccountToken] = {}
        self._lock = threading.Lock()
        self._total_refreshes = 0
        self._total_validations = 0

    # ─── Token Lifecycle ───────────────────────────────────

    def register_token(self, account_id: str, access_token: str,
                        refresh_token: str = "", scope: str = "",
                        expires_in: int = 3600 * 24 * 30) -> AccountToken:
        """Register a new OAuth token for an account."""
        token = AccountToken(
            access_token=access_token,
            refresh_token=refresh_token,
            scope=scope or AccountToken.scope,
            expires_in=expires_in,
        )
        with self._lock:
            self._tokens[account_id] = token
        return token

    def get_token(self, account_id: str) -> Optional[AccountToken]:
        """Get token for an account."""
        return self._tokens.get(account_id)

    def remove_token(self, account_id: str) -> bool:
        """Remove token for an account."""
        with self._lock:
            return self._tokens.pop(account_id, None) is not None

    # ─── Token Validation ──────────────────────────────────

    def validate_token(self, account_id: str) -> Tuple[bool, str]:
        """Validate token and return (is_valid, message)."""
        token = self._tokens.get(account_id)
        if not token:
            return False, "No token registered"

        with self._lock:
            self._total_validations += 1

        if not token.access_token:
            return False, "Access token is empty"

        if token.is_expired:
            return False, f"Token expired {token.days_until_expiry} days ago"

        if not token.is_valid:
            return False, f"Token marked invalid: {token.error_message}"

        return True, "Token is valid"

    def refresh_token(self, account_id: str) -> Optional[AccountToken]:
        """Simulate token refresh. In production, calls Pinterest API."""
        token = self._tokens.get(account_id)
        if not token:
            return None

        if not token.refresh_token:
            raise InvalidTokenError("No refresh token available")

        # Simulate refresh
        with self._lock:
            token.issued_at = time.time()
            token.last_refreshed = time.time()
            token.refresh_count += 1
            token.is_valid = True
            self._total_refreshes += 1

        return token

    def invalidate_token(self, account_id: str, error: str = "") -> None:
        """Mark a token as invalid."""
        token = self._tokens.get(account_id)
        if token:
            with self._lock:
                token.is_valid = False
                token.error_message = error

    def check_expiry_all(self) -> Dict[str, Any]:
        """Check expiry status of all tokens. Returns summary."""
        expired = []
        expiring_soon = []
        healthy = []

        for account_id, token in self._tokens.items():
            if token.is_expired:
                expired.append(account_id)
            elif token.should_refresh:
                expiring_soon.append(account_id)
            else:
                healthy.append(account_id)

        return {
            "total": len(self._tokens),
            "healthy": len(healthy),
            "expiring_soon": len(expiring_soon),
            "expired": len(expired),
            "expired_ids": expired,
            "expiring_ids": expiring_soon,
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_tokens": len(self._tokens),
            "total_refreshes": self._total_refreshes,
            "total_validations": self._total_validations,
            "expiry_summary": self.check_expiry_all(),
        }
