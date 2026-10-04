"""Persistent authenticated browser session contract for Layer 10 affiliate flows.

Credentials/passwords never enter this layer. The browser worker owns the
persistent profile/session. Layer 10 receives only provider/account-scoped
evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


class AffiliateSessionError(RuntimeError):
    """Raised when an authenticated affiliate browser session is unavailable."""


@dataclass(frozen=True)
class AffiliateAccountProfile:
    provider: str
    account_ref: str
    marketplace: str | None = None


@dataclass(frozen=True)
class AffiliateSessionStatus:
    provider: str
    account_ref: str
    authenticated: bool
    persistent: bool
    evidence: Mapping[str, Any]


class PersistentAffiliateBrowser(Protocol):
    def session_status(self, account: AffiliateAccountProfile) -> AffiliateSessionStatus:
        ...

    def search_and_get_affiliate_link(
        self, account: AffiliateAccountProfile, query: str
    ) -> Mapping[str, Any]:
        ...


class AffiliateAccountService:
    """One-time-login account facade.

    The first call may report authenticated=False. The user then completes
    provider login through the browser worker's interactive onboarding surface.
    Subsequent tasks reuse the same named persistent browser profile.
    """

    def __init__(self, browser: PersistentAffiliateBrowser) -> None:
        self._browser = browser

    def status(self, account: AffiliateAccountProfile) -> AffiliateSessionStatus:
        return self._browser.session_status(account)

    def require_authenticated(
        self, account: AffiliateAccountProfile
    ) -> AffiliateSessionStatus:
        status = self.status(account)
        if not status.persistent:
            raise AffiliateSessionError("affiliate browser profile is not persistent")
        if not status.authenticated:
            raise AffiliateSessionError(
                f"affiliate account '{account.account_ref}' requires one-time login"
            )
        return status

    def find_product_link(
        self, account: AffiliateAccountProfile, query: str
    ) -> Mapping[str, Any]:
        self.require_authenticated(account)
        if not query.strip():
            raise ValueError("query is required")
        result = self._browser.search_and_get_affiliate_link(account, query)
        if not isinstance(result, Mapping) or not result.get("affiliate_url"):
            raise AffiliateSessionError("browser returned no real affiliate URL")
        return result
