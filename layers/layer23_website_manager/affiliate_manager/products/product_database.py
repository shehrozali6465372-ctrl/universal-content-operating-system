"""ProductDatabase — Store, search, and manage affiliate products."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.affiliate_manager.models.affiliate_models import (
    AffiliateProduct, ProductStatus,
)
from layers.layer23_website_manager.affiliate_manager.exceptions import ProductNotFoundError


class ProductDatabase:
    """CRUD and search for affiliate products by niche, category, price, rating."""

    # Preset products by niche
    PRESET_PRODUCTS: Dict[str, List[Dict[str, Any]]] = {
        "home_decor": [
            {"name": "Platform Bed Frame", "price": 299.99, "rating": 4.5, "niche": "home_decor",
             "category": "furniture", "commission": 6.0},
            {"name": "LED Strip Lights", "price": 19.99, "rating": 4.3, "niche": "home_decor",
             "category": "lighting", "commission": 5.0},
            {"name": "Memory Foam Mattress", "price": 399.99, "rating": 4.7, "niche": "home_decor",
             "category": "bedroom", "commission": 8.0},
            {"name": "Curtain Set Blackout", "price": 34.99, "rating": 4.4, "niche": "home_decor",
             "category": "window", "commission": 4.0},
            {"name": "Wall Art Canvas Set", "price": 29.99, "rating": 4.2, "niche": "home_decor",
             "category": "decor", "commission": 5.0},
        ],
        "fashion": [
            {"name": "Casual Blazer Women", "price": 89.99, "rating": 4.4, "niche": "fashion",
             "category": "clothing", "commission": 7.0},
            {"name": "Leather Crossbody Bag", "price": 59.99, "rating": 4.6, "niche": "fashion",
             "category": "accessories", "commission": 8.0},
        ],
        "beauty": [
            {"name": "Vitamin C Serum", "price": 24.99, "rating": 4.5, "niche": "beauty",
             "category": "skincare", "commission": 10.0},
            {"name": "Retinol Moisturizer", "price": 34.99, "rating": 4.3, "niche": "beauty",
             "category": "skincare", "commission": 8.0},
        ],
        "food": [
            {"name": "Air Fryer Oven", "price": 129.99, "rating": 4.6, "niche": "food",
             "category": "kitchen", "commission": 6.0},
            {"name": "Instant Pot Duo", "price": 89.99, "rating": 4.7, "niche": "food",
             "category": "kitchen", "commission": 5.0},
        ],
        "tech": [
            {"name": "Wireless Earbuds Pro", "price": 79.99, "rating": 4.4, "niche": "tech",
             "category": "audio", "commission": 4.0},
            {"name": "Portable Charger 20000mAh", "price": 39.99, "rating": 4.5, "niche": "tech",
             "category": "accessories", "commission": 5.0},
        ],
        "fitness": [
            {"name": "Premium Yoga Mat", "price": 49.99, "rating": 4.6, "niche": "fitness",
             "category": "equipment", "commission": 5.0},
            {"name": "Resistance Bands Set", "price": 19.99, "rating": 4.4, "niche": "fitness",
             "category": "equipment", "commission": 6.0},
        ],
        "travel": [
            {"name": "Travel Backpack 40L", "price": 79.99, "rating": 4.5, "niche": "travel",
             "category": "luggage", "commission": 6.0},
            {"name": "Passport Holder Wallet", "price": 14.99, "rating": 4.3, "niche": "travel",
             "category": "accessories", "commission": 4.0},
        ],
        "finance": [
            {"name": "Personal Finance Book", "price": 19.99, "rating": 4.4, "niche": "finance",
             "category": "books", "commission": 4.0},
        ],
        "diy": [
            {"name": "Power Tool Combo Kit", "price": 149.99, "rating": 4.6, "niche": "diy",
             "category": "tools", "commission": 5.0},
            {"name": "Craft Supplies Bundle", "price": 29.99, "rating": 4.2, "niche": "diy",
             "category": "crafts", "commission": 6.0},
        ],
    }

    def __init__(self) -> None:
        self._products: Dict[str, AffiliateProduct] = {}
        self._lock = threading.Lock()

    def load_presets(self, merchant_id: str = "", network_id: str = "") -> int:
        """Load preset products by niche. Returns count."""
        count = 0
        for niche, products in self.PRESET_PRODUCTS.items():
            for pdata in products:
                product = self.add_product(
                    product_name=pdata["name"],
                    price=pdata["price"],
                    category=pdata["category"],
                    niche=pdata["niche"],
                    rating=pdata["rating"],
                    commission_rate=pdata["commission"],
                    merchant_id=merchant_id,
                    network_id=network_id,
                )
                self._products[product.product_id] = product
                count += 1
        return count

    def add_product(self, product_name: str, price: float = 0.0,
                     category: str = "", niche: str = "",
                     rating: float = 0.0, commission_rate: float = 0.0,
                     affiliate_link: str = "", merchant_id: str = "",
                     network_id: str = "") -> AffiliateProduct:
        """Add a product to the database."""
        product = AffiliateProduct(
            product_name=product_name,
            price=price,
            category=category,
            niche=niche,
            rating=rating,
            commission_rate=commission_rate,
            affiliate_link=affiliate_link,
            merchant_id=merchant_id,
            network_id=network_id,
            status=ProductStatus.IN_STOCK,
        )
        with self._lock:
            self._products[product.product_id] = product
        return product

    def get_product(self, product_id: str) -> Optional[AffiliateProduct]:
        return self._products.get(product_id)

    def search_by_niche(self, niche: str, min_rating: float = 0.0,
                         max_price: float = 99999.0) -> List[AffiliateProduct]:
        """Search products by niche with rating and price filters."""
        results = []
        for p in self._products.values():
            if p.niche == niche and p.rating >= min_rating and p.price <= max_price:
                if p.is_available:
                    results.append(p)
        return sorted(results, key=lambda p: p.rating, reverse=True)

    def search_by_keyword(self, keyword: str) -> List[AffiliateProduct]:
        kw = keyword.lower()
        return [p for p in self._products.values()
                if kw in p.product_name.lower() or kw in p.category.lower()]

    def get_all_products(self, niche: str = "") -> List[AffiliateProduct]:
        if niche:
            return [p for p in self._products.values() if p.niche == niche]
        return list(self._products.values())

    def update_stats(self, product_id: str, clicks: int = 0,
                      sales: int = 0, commission: float = 0.0) -> bool:
        product = self._products.get(product_id)
        if not product:
            return False
        with self._lock:
            product.total_clicks += clicks
            product.total_sales += sales
            product.total_commission += commission
            if product.total_clicks > 0:
                product.conversion_rate = (product.total_sales / product.total_clicks) * 100
        return True

    def get_top_products(self, niche: str = "", top_k: int = 5) -> List[AffiliateProduct]:
        products = self.get_all_products(niche)
        return sorted(products, key=lambda p: p.rating * p.commission_rate, reverse=True)[:top_k]

    def get_stats(self) -> Dict[str, Any]:
        by_niche: Dict[str, int] = {}
        for p in self._products.values():
            by_niche[p.niche] = by_niche.get(p.niche, 0) + 1
        return {
            "total_products": len(self._products),
            "by_niche": by_niche,
            "total_commission": sum(p.total_commission for p in self._products.values()),
        }
