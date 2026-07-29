"""Affiliate data models — networks, merchants, products, clicks, links."""
from __future__ import annotations
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


class NetworkStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


class ProductStatus(str, Enum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"
    PENDING = "pending"


class LinkType(str, Enum):
    DEEP_LINK = "deep_link"
    SHORT_LINK = "short_link"
    TRACKING_LINK = "tracking_link"
    COUNTRY_LINK = "country_link"


@dataclass
class AffiliateNetwork:
    """Affiliate network program — Amazon, Impact, CJ, ShareASale, etc."""

    network_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    network_name: str = ""
    api_key: str = ""
    api_secret: str = ""
    status: NetworkStatus = NetworkStatus.PENDING
    country: str = "US"
    supported_currencies: List[str] = field(default_factory=lambda: ["USD"])
    commission_rate: float = 0.0
    cookie_days: int = 30
    min_payout: float = 50.0
    total_earnings: float = 0.0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    @property
    def is_active(self) -> bool:
        return self.status == NetworkStatus.ACTIVE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "network_id": self.network_id,
            "network_name": self.network_name,
            "status": self.status.value,
            "country": self.country,
            "commission_rate": self.commission_rate,
            "cookie_days": self.cookie_days,
            "min_payout": self.min_payout,
            "total_earnings": round(self.total_earnings, 2),
        }


@dataclass
class Merchant:
    """Individual merchant/brand within an affiliate network."""

    merchant_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    network_id: str = ""
    merchant_name: str = ""
    website: str = ""
    commission_rate: float = 0.0
    cookie_days: int = 30
    status: NetworkStatus = NetworkStatus.PENDING
    category: str = ""
    country: str = "US"
    rating: float = 0.0
    total_sales: int = 0
    total_commission: float = 0.0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "merchant_id": self.merchant_id,
            "merchant_name": self.merchant_name,
            "website": self.website,
            "commission_rate": self.commission_rate,
            "cookie_days": self.cookie_days,
            "status": self.status.value,
            "category": self.category,
            "rating": self.rating,
        }


@dataclass
class AffiliateProduct:
    """Affiliate product with pricing, ratings, and affiliate link."""

    product_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    merchant_id: str = ""
    network_id: str = ""
    product_name: str = ""
    category: str = ""
    price: float = 0.0
    currency: str = "USD"
    affiliate_link: str = ""
    direct_url: str = ""
    image_url: str = ""
    rating: float = 0.0
    review_count: int = 0
    status: ProductStatus = ProductStatus.PENDING
    commission_rate: float = 0.0
    commission_type: str = "percentage"
    niche: str = ""
    keywords: List[str] = field(default_factory=list)
    total_clicks: int = 0
    total_sales: int = 0
    total_commission: float = 0.0
    conversion_rate: float = 0.0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    @property
    def epc(self) -> float:
        """Earnings per click."""
        if self.total_clicks == 0:
            return 0.0
        return round(self.total_commission / self.total_clicks, 4)

    @property
    def is_available(self) -> bool:
        return self.status == ProductStatus.IN_STOCK

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "category": self.category,
            "price": self.price,
            "rating": self.rating,
            "commission_rate": self.commission_rate,
            "niche": self.niche,
            "total_clicks": self.total_clicks,
            "total_sales": self.total_sales,
            "total_commission": round(self.total_commission, 2),
            "conversion_rate": round(self.conversion_rate, 2),
            "epc": round(self.epc, 4),
            "status": self.status.value,
        }


@dataclass
class AffiliateClick:
    """Track a single click/sale event for an affiliate product."""

    click_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    product_id: str = ""
    article_id: str = ""
    pin_id: str = ""
    source: str = ""  # website, pinterest, direct
    click_time: float = field(default_factory=time.time)
    converted: bool = False
    sale_amount: float = 0.0
    commission: float = 0.0
    country: str = ""
    user_agent: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "click_id": self.click_id,
            "product_id": self.product_id,
            "source": self.source,
            "converted": self.converted,
            "sale_amount": self.sale_amount,
            "commission": self.commission,
        }


@dataclass
class AffiliateLink:
    """Generated affiliate link with metadata."""

    link_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    product_id: str = ""
    original_url: str = ""
    affiliate_url: str = ""
    short_url: str = ""
    link_type: LinkType = LinkType.DEEP_LINK
    is_active: bool = True
    total_clicks: int = 0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "link_id": self.link_id,
            "product_id": self.product_id,
            "affiliate_url": self.affiliate_url,
            "link_type": self.link_type.value,
            "is_active": self.is_active,
            "total_clicks": self.total_clicks,
        }
