"""Layer 14 implementation of the Layer 10 affiliate browser contract.

The worker receives only a persistent profile reference. Credentials and cookies
stay inside the browser worker profile. This adapter never accepts passwords or
creates affiliate URLs locally.
"""
from __future__ import annotations

import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Any, Mapping
from urllib.parse import quote_plus, urlsplit

from layers.layer10_monetization.modules.affiliate_browser import (
    AffiliateBrowserGateway,
    AffiliateLink,
    AffiliateProduct,
    AffiliateSearchRequest,
    AffiliateSearchResult,
)



def browser_request_from_environment(method: str, path: str, payload: dict[str, Any] | None = None, timeout: float = 75.0):
    """Call the authenticated UCOS browser worker without exposing credentials to Layer 10."""
    base=os.environ.get("UCOS_BROWSER_WORKER_URL", "").strip().rstrip("/")
    token=os.environ.get("UCOS_BROWSER_TOKEN", "").strip()
    if not base or not token:
        raise RuntimeError("UCOS browser worker is not configured")
    body=json.dumps(payload or {}).encode("utf-8")
    request=Request(
        f"{base}{path}",
        data=body if method != "GET" else None,
        method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read(2_000_000).decode("utf-8"))
    except HTTPError as exc:
        raw=exc.read(2_000_000)
        try:
            data=json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            data={"error": str(exc)}
        return exc.code, data
    except URLError as exc:
        raise RuntimeError(f"browser worker unavailable: {exc.reason}") from exc


class PersonalBrowserAffiliateGateway(AffiliateBrowserGateway):
    """Execute bounded affiliate discovery through the authenticated browser worker."""

    def __init__(self, browser_request) -> None:
        self._browser_request = browser_request

    @staticmethod
    def _amazon_host(value: str) -> bool:
        host = (urlsplit(value).hostname or "").lower().rstrip(".")
        return bool(re.fullmatch(r"(?:[a-z0-9-]+\.)*amazon\.[a-z.]+", host))

    @staticmethod
    def _product_ref(url: str) -> str:
        path = urlsplit(url).path.upper()
        match = re.search(r"/DP/([A-Z0-9]{10})(?:/|$)", path)
        return match.group(1) if match else ""

    def _execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        status, result = self._browser_request("POST", "/execute", payload)
        if status >= 400:
            raise RuntimeError(str(result.get("error", "browser worker task failed")))
        return result.get("result", result)

    def search_products(self, request: AffiliateSearchRequest) -> AffiliateSearchResult:
        marketplace = (request.marketplace or "www.amazon.com").strip().lower()
        if not self._amazon_host("https://" + marketplace):
            raise ValueError("unsupported Amazon marketplace host")
        search_url = f"https://{marketplace}/s?k={quote_plus(request.query)}"
        result = self._execute({
            "url": search_url,
            "profile_ref": request.account_ref,
            "actions": [{"type": "extract"}],
        })

        products: list[AffiliateProduct] = []
        seen: set[str] = set()
        for item in result.get("links", []):
            href = str(item.get("href", "")).strip()
            if not href or not self._amazon_host(href):
                continue
            ref = self._product_ref(href)
            if not ref or ref in seen:
                continue
            seen.add(ref)
            products.append(
                AffiliateProduct(
                    product_ref=ref,
                    title=str(item.get("text", "")).strip() or ref,
                    product_url=href,
                )
            )
            if len(products) >= request.max_results:
                break

        return AffiliateSearchResult(
            provider=request.provider,
            account_ref=request.account_ref,
            products=tuple(products),
            source="authenticated_browser",
        )

    def create_affiliate_link(
        self, *, account_ref: str, product: AffiliateProduct
    ) -> AffiliateLink:
        # SiteStripe is the approved browser-side path for generating a tagged
        # link from the current Amazon product page. The selector is configurable
        # because Amazon can change its UI without changing the affiliate contract.
        selector = (
            __import__("os").environ.get(
                "UCOS_AMAZON_SITESTRIPE_SELECTOR",
                "[data-testid*='get-link'], [id*='get-link'], button:has-text('Get Link')",
            ).strip()
        )
        result = self._execute({
            "url": product.product_url,
            "profile_ref": account_ref,
            "actions": [
                {"type": "extract"},
                {"type": "click", "selector": selector},
                {"type": "wait", "ms": 750},
                {"type": "extract"},
            ],
        })

        candidates: list[str] = []
        for item in result.get("links", []):
            href = str(item.get("href", "")).strip()
            if self._amazon_host(href) and "tag=" in href:
                candidates.append(href)

        # Some SiteStripe releases expose the generated URL as text rather than
        # an anchor. Accept only a real HTTPS Amazon URL containing a tag.
        text = str(result.get("text", ""))
        candidates.extend(
            re.findall(r"https://(?:[a-z0-9-]+\.)*amazon\.[a-z.]+[^\s<>\"']*tag=[^\s<>\"']+", text, re.I)
        )

        affiliate_url = next((u for u in candidates if self._product_ref(u) in {"", product.product_ref}), "")
        if not affiliate_url:
            raise RuntimeError(
                "authenticated Amazon SiteStripe did not return a tagged product link"
            )

        return AffiliateLink(
            provider="amazon",
            account_ref=account_ref,
            product_ref=product.product_ref,
            affiliate_url=affiliate_url,
            source="authenticated_browser",
            evidence={
                "method": "amazon_sitestripe",
                "product_title": product.title,
                "product_url": product.product_url,
                "profile_ref": account_ref,
                "final_url": result.get("final_url"),
            },
        )


__all__ = ["PersonalBrowserAffiliateGateway", "browser_request_from_environment"]
