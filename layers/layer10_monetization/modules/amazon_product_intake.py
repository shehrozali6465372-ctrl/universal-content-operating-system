"""Amazon Associates product intake for UCOS.

This module intentionally does not automate Amazon browsing or create Amazon
sessions. Products/affiliate links must come from an Amazon-approved linking
workflow (for example SiteStripe or Mobile GetLink) and are then handed to UCOS.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import parse_qs, urlsplit


_ASIN_RE = re.compile(r"^[A-Z0-9]{10}$")
_AMAZON_HOST_RE = re.compile(r"(?:^|\.)amazon\.[a-z.]+$", re.IGNORECASE)


@dataclass(frozen=True)
class AmazonProductIntake:
    product_name: str
    product_url: str
    affiliate_link: str
    asin: str
    niche: str = ""
    tracking_id: str = ""
    marketplace: str = ""
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _is_amazon_url(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme == "https" and bool(parsed.hostname) and bool(
        _AMAZON_HOST_RE.fullmatch(parsed.hostname.lower())
    )


def _extract_asin(url: str) -> str:
    parsed = urlsplit(url)
    path = parsed.path.upper()
    patterns = (
        r"/DP/([A-Z0-9]{10})(?:/|$)",
        r"/GP/PRODUCT/([A-Z0-9]{10})(?:/|$)",
        r"/PRODUCT/([A-Z0-9]{10})(?:/|$)",
    )
    for pattern in patterns:
        match = re.search(pattern, path)
        if match and _ASIN_RE.fullmatch(match.group(1)):
            return match.group(1)
    return ""


def normalize_amazon_product(
    *,
    product_name: str,
    product_url: str,
    affiliate_link: str,
    asin: str = "",
    niche: str = "",
    marketplace: str = "",
    metadata: dict[str, Any] | None = None,
) -> AmazonProductIntake:
    product_name = str(product_name or "").strip()
    product_url = str(product_url or "").strip()
    affiliate_link = str(affiliate_link or "").strip()
    asin = str(asin or "").strip().upper()

    if not product_name:
        raise ValueError("product_name is required")
    if not _is_amazon_url(product_url):
        raise ValueError("product_url must be an HTTPS Amazon product URL")
    if not _is_amazon_url(affiliate_link):
        raise ValueError("affiliate_link must be an HTTPS Amazon URL")

    detected = _extract_asin(product_url)
    if asin and not _ASIN_RE.fullmatch(asin):
        raise ValueError("asin must be a 10-character Amazon ASIN")
    if not asin:
        asin = detected
    if not asin:
        raise ValueError("ASIN could not be determined from product_url; provide asin")

    params = parse_qs(urlsplit(affiliate_link).query)
    tracking_id = (params.get("tag") or [""])[0].strip()
    if not tracking_id:
        raise ValueError("affiliate_link must contain an Amazon Associates tracking tag")

    return AmazonProductIntake(
        product_name=product_name,
        product_url=product_url,
        affiliate_link=affiliate_link,
        asin=asin,
        niche=str(niche or "").strip(),
        tracking_id=tracking_id,
        marketplace=str(marketplace or "").strip(),
        metadata=dict(metadata or {}),
    )
