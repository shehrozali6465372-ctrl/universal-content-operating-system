"""MerchantManager — Manage merchants/brands within affiliate networks."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.affiliate_manager.models.affiliate_models import (
    Merchant, NetworkStatus,
)
from layers.layer23_website_manager.affiliate_manager.exceptions import MerchantNotFoundError


class MerchantManager:
    """Register, update, and manage affiliate merchants/brands."""

    PRESET_MERCHANTS: List[Dict[str, Any]] = [
        {"name": "Amazon", "network": "Amazon Associates", "commission": 6.0, "category": "general"},
        {"name": "Nike", "network": "Impact", "commission": 5.0, "category": "fashion"},
        {"name": "Temu", "network": "Impact", "commission": 10.0, "category": "general"},
        {"name": "AliExpress", "network": "Impact", "commission": 8.0, "category": "general"},
        {"name": "Etsy", "network": "Awin", "commission": 4.0, "category": "diy"},
        {"name": "Wayfair", "network": "CJ Affiliate", "commission": 5.0, "category": "home_decor"},
        {"name": "Sephora", "network": "CJ Affiliate", "commission": 6.0, "category": "beauty"},
        {"name": "Walmart", "network": "Impact", "commission": 4.0, "category": "general"},
        {"name": "Target", "network": "ShareASale", "commission": 4.0, "category": "general"},
        {"name": "eBay", "network": "Awin", "commission": 3.0, "category": "general"},
    ]

    def __init__(self) -> None:
        self._merchants: Dict[str, Merchant] = {}
        self._lock = threading.Lock()

    def register_merchant(self, merchant_name: str, network_id: str = "",
                            website: str = "", commission_rate: float = 0.0,
                            category: str = "", country: str = "US") -> Merchant:
        """Register a new merchant."""
        merchant = Merchant(
            merchant_name=merchant_name,
            network_id=network_id,
            website=website,
            commission_rate=commission_rate,
            category=category,
            country=country,
        )
        with self._lock:
            self._merchants[merchant.merchant_id] = merchant
        return merchant

    def get_merchant(self, merchant_id: str) -> Optional[Merchant]:
        return self._merchants.get(merchant_id)

    def get_merchants_by_network(self, network_id: str) -> List[Merchant]:
        return [m for m in self._merchants.values() if m.network_id == network_id]

    def get_merchants_by_category(self, category: str) -> List[Merchant]:
        return [m for m in self._merchants.values() if m.category == category]

    def get_all_merchants(self) -> List[Merchant]:
        return list(self._merchants.values())

    def update_merchant(self, merchant_id: str, **kwargs) -> Optional[Merchant]:
        merchant = self._merchants.get(merchant_id)
        if not merchant:
            return None
        allowed = {"merchant_name", "website", "commission_rate", "cookie_days", "category", "status", "rating"}
        for key, value in kwargs.items():
            if key in allowed:
                setattr(merchant, key, value)
        return merchant

    def delete_merchant(self, merchant_id: str) -> bool:
        return self._merchants.pop(merchant_id, None) is not None

    def get_stats(self) -> Dict[str, Any]:
        by_cat: Dict[str, int] = {}
        for m in self._merchants.values():
            by_cat[m.category] = by_cat.get(m.category, 0) + 1
        return {
            "total_merchants": len(self._merchants),
            "by_category": by_cat,
        }
