"""Amazon Associates browser workflow contract.

The worker owns the persistent authenticated browser profile. This adapter
describes the allowed high-level flow and validates evidence; it never stores
Amazon passwords, session cookies, or fabricated affiliate URLs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol
from urllib.parse import urlsplit


class AmazonAffiliateBrowserError(RuntimeError):
    pass


@dataclass(frozen=True)
class AmazonBrowserAccount:
    account_ref: str
    marketplace: str = "www.amazon.com"


class AmazonAffiliateBrowser(Protocol):
    def status(self, account: AmazonBrowserAccount) -> Mapping[str, Any]:
        ...

    def search(self, account: AmazonBrowserAccount, query: str) -> Mapping[str, Any]:
        ...

    def get_link(
        self, account: AmazonBrowserAccount, product: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        ...


class AmazonAffiliateService:
    def __init__(self, browser: AmazonAffiliateBrowser) -> None:
        self._browser = browser

    def search_and_get_link(
        self, account: AmazonBrowserAccount, query: str
    ) -> Mapping[str, Any]:
        status = self._browser.status(account)
        if not status.get("authenticated"):
            raise AmazonAffiliateBrowserError(
                "Amazon Associates account requires one-time browser login"
            )
        products = self._browser.search(account, query)
        product = products.get("product") if isinstance(products, Mapping) else None
        if not isinstance(product, Mapping):
            raise AmazonAffiliateBrowserError("Amazon search returned no product")
        link = self._browser.get_link(account, product)
        affiliate_url = str(link.get("affiliate_url", "")).strip()
        if urlsplit(affiliate_url).scheme != "https" or not urlsplit(affiliate_url).netloc:
            raise AmazonAffiliateBrowserError("Amazon affiliate URL must be HTTPS")
        if not link.get("evidence"):
            raise AmazonAffiliateBrowserError("affiliate link requires browser evidence")
        return link
