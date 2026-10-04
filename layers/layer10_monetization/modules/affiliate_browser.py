"""Secure browser-assisted affiliate discovery for Layer 10.

Layer 10 decides *what* affiliate product/link is required. It never owns
affiliate credentials and never fabricates a URL. An injected browser client
performs the authenticated website interaction behind the Layer 17/browser
security boundary and returns evidence from the affiliate account.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol
from urllib.parse import urlparse


class BrowserAffiliateError(RuntimeError):
    """Raised when an affiliate acquisition cannot be proven real."""


@dataclass(frozen=True)
class AffiliateSearchRequest:
    provider: str
    query: str
    account_ref: str
    marketplace: str | None = None
    max_results: int = 10

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("provider is required")
        if not self.query.strip():
            raise ValueError("query is required")
        if not self.account_ref.strip():
            raise ValueError("account_ref is required")
        if self.max_results < 1 or self.max_results > 50:
            raise ValueError("max_results must be between 1 and 50")


@dataclass(frozen=True)
class AffiliateProduct:
    product_ref: str
    title: str
    product_url: str
    price: str | None = None
    currency: str | None = None
    image_url: str | None = None


@dataclass(frozen=True)
class AffiliateSearchResult:
    provider: str
    account_ref: str
    products: tuple[AffiliateProduct, ...]
    source: str = "authenticated_browser"


@dataclass(frozen=True)
class AffiliateLink:
    provider: str
    account_ref: str
    product_ref: str
    affiliate_url: str
    source: str
    evidence: Mapping[str, Any]


class AffiliateBrowserGateway(Protocol):
    """Public browser contract; credential handling remains outside Layer 10."""

    def search_products(self, request: AffiliateSearchRequest) -> AffiliateSearchResult:
        ...

    def create_affiliate_link(
        self, *, account_ref: str, product: AffiliateProduct
    ) -> AffiliateLink:
        ...


class AffiliateBrowserClient:
    """Layer-10 orchestration over an authenticated browser gateway."""

    def __init__(self, gateway: AffiliateBrowserGateway) -> None:
        self._gateway = gateway

    def search_and_get_link(self, request: AffiliateSearchRequest) -> AffiliateLink:
        result = self._gateway.search_products(request)
        self._validate_search_result(request, result)
        product = result.products[0]
        link = self._gateway.create_affiliate_link(
            account_ref=request.account_ref, product=product
        )
        self._validate_link(request, product, link)
        return link

    @staticmethod
    def _validate_search_result(
        request: AffiliateSearchRequest, result: AffiliateSearchResult
    ) -> None:
        if result.source != "authenticated_browser":
            raise BrowserAffiliateError("affiliate result lacks authenticated-browser provenance")
        if result.provider != request.provider or result.account_ref != request.account_ref:
            raise BrowserAffiliateError("affiliate result account/provider mismatch")
        if not result.products:
            raise BrowserAffiliateError("affiliate account returned no matching product")

    @staticmethod
    def _validate_link(
        request: AffiliateSearchRequest,
        product: AffiliateProduct,
        link: AffiliateLink,
    ) -> None:
        if link.source != "authenticated_browser":
            raise BrowserAffiliateError("affiliate link lacks authenticated-browser provenance")
        if link.provider != request.provider or link.account_ref != request.account_ref:
            raise BrowserAffiliateError("affiliate link account/provider mismatch")
        if link.product_ref != product.product_ref:
            raise BrowserAffiliateError("affiliate link is not bound to selected product")
        parsed = urlparse(link.affiliate_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise BrowserAffiliateError("affiliate URL must be a valid HTTPS URL")
        if not link.evidence:
            raise BrowserAffiliateError("affiliate link requires source evidence")


__all__ = [
    "AffiliateBrowserClient",
    "AffiliateLink",
    "AffiliateProduct",
    "AffiliateSearchRequest",
    "AffiliateSearchResult",
    "BrowserAffiliateError",
]
