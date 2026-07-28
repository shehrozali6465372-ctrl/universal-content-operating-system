"""AccountToken — OAuth token management data model."""
from __future__ import annotations
import time
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class AccountToken:
    """OAuth 2.0 token for Pinterest API access."""

    access_token: str = ""
    refresh_token: str = ""
    token_type: str = "bearer"
    scope: str = "boards:read,boards:write,pins:read,pins:write"
    expires_in: int = 3600 * 24 * 30  # 30 days default
    issued_at: float = field(default_factory=time.time)
    last_refreshed: float = 0.0
    refresh_count: int = 0
    is_valid: bool = True
    error_message: str = ""

    @property
    def expiry_time(self) -> float:
        return self.issued_at + self.expires_in

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expiry_time

    @property
    def time_until_expiry(self) -> float:
        remaining = self.expiry_time - time.time()
        return max(0.0, remaining)

    @property
    def days_until_expiry(self) -> float:
        return round(self.time_until_expiry / 86400, 1)

    @property
    def should_refresh(self) -> bool:
        """Refresh if less than 7 days remaining or already expired."""
        return self.days_until_expiry < 7 or self.is_expired

    def to_dict(self) -> Dict[str, Any]:
        return {
            "access_token": f"{self.access_token[:8]}...{self.access_token[-4:]}" if self.access_token else "",
            "refresh_token": f"{self.refresh_token[:8]}..." if self.refresh_token else "",
            "token_type": self.token_type,
            "scope": self.scope,
            "expires_in": self.expires_in,
            "days_until_expiry": self.days_until_expiry,
            "is_expired": self.is_expired,
            "should_refresh": self.should_refresh,
            "issued_at": self.issued_at,
            "last_refreshed": self.last_refreshed,
            "refresh_count": self.refresh_count,
            "is_valid": self.is_valid,
        }
