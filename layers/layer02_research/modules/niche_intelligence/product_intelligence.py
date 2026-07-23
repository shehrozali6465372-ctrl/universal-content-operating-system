"""ProductIntelligence — Best-selling products, high commission, recurring SaaS, seasonal."""
from __future__ import annotations
import threading
import time
import uuid
from typing import Any, Dict, List, Optional


class ProductProfile:
    __slots__ = ("id", "name", "category", "brand", "price", "commission_rate",
                 "commission_type", "recurring", "recurring_interval", "recurring_value",
                 "affiliate_program", "product_url", "rating", "review_count",
                 "best_seller_rank", "seasonal", "peak_months", "tags", "score")

    def __init__(self, name: str, category: str = "", brand: str = "",
                 price: float = 0.0) -> None:
        self.id = str(uuid.uuid4())[:12]
        self.name = name
        self.category = category
        self.brand = brand
        self.price = price
        self.commission_rate = 0.0
        self.commission_type = "percentage"
        self.recurring = False
        self.recurring_interval = "monthly"
        self.recurring_value = 0.0
        self.affiliate_program = ""
        self.product_url = ""
        self.rating = 0.0
        self.review_count = 0
        self.best_seller_rank = 0
        self.seasonal = False
        self.peak_months: List[int] = []
        self.tags: List[str] = []
        self.score = 0.0

    @property
    def commission_per_sale(self) -> float:
        if self.commission_type == "fixed":
            return self.commission_rate
        return self.price * (self.commission_rate / 100)

    @property
    def annual_recurring_value(self) -> float:
        if not self.recurring:
            return 0.0
        intervals = {"monthly": 12, "quarterly": 4, "yearly": 1, "weekly": 52}
        return self.recurring_value * intervals.get(self.recurring_interval, 12)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "category": self.category,
            "brand": self.brand, "price": round(self.price, 2),
            "commission_rate": self.commission_rate,
            "commission_type": self.commission_type,
            "commission_per_sale": round(self.commission_per_sale, 2),
            "recurring": self.recurring,
            "annual_recurring": round(self.annual_recurring_value, 2),
            "affiliate_program": self.affiliate_program,
            "rating": round(self.rating, 1),
            "review_count": self.review_count,
            "best_seller_rank": self.best_seller_rank,
            "seasonal": self.seasonal,
            "score": round(self.score, 1),
        }


class ProductIntelligence:
    """Discovers and scores products for affiliate monetization."""
    _instance: Optional["ProductIntelligence"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ProductIntelligence":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._products: Dict[str, ProductProfile] = {}
        self._category_index: Dict[str, List[str]] = {}
        self._program_index: Dict[str, List[str]] = {}

    def add_product(self, name: str, category: str, brand: str = "",
                    price: float = 0.0, commission_rate: float = 0.0,
                    commission_type: str = "percentage", program: str = "",
                    rating: float = 0.0, review_count: int = 0,
                    recurring: bool = False, recurring_value: float = 0.0,
                    tags: List[str] = None) -> ProductProfile:
        p = ProductProfile(name, category, brand, price)
        p.commission_rate = commission_rate
        p.commission_type = commission_type
        p.affiliate_program = program
        p.rating = rating
        p.review_count = review_count
        p.recurring = recurring
        p.recurring_value = recurring_value
        p.tags = tags or []
        p.score = self._score_product(p)
        self._products[p.id] = p
        self._category_index.setdefault(category, []).append(p.id)
        if program:
            self._program_index.setdefault(program, []).append(p.id)
        return p

    def _score_product(self, p: ProductProfile) -> float:
        commission_score = min(p.commission_per_sale / 50, 1.0) * 35
        rating_score = (p.rating / 5.0) * 20 if p.rating > 0 else 10
        review_score = min(p.review_count / 1000, 1.0) * 15
        recurring_bonus = 15 if p.recurring else 0
        bestseller_bonus = min(max(100 - p.best_seller_rank, 0) / 100, 1.0) * 15 if p.best_seller_rank > 0 else 0
        return commission_score + rating_score + review_score + recurring_bonus + bestseller_bonus

    def get_product(self, product_id: str) -> Optional[ProductProfile]:
        return self._products.get(product_id)

    def get_by_category(self, category: str) -> List[ProductProfile]:
        ids = self._category_index.get(category, [])
        return sorted(
            [self._products[i] for i in ids if i in self._products],
            key=lambda p: p.score, reverse=True,
        )

    def get_by_program(self, program: str) -> List[ProductProfile]:
        ids = self._program_index.get(program, [])
        return [self._products[i] for i in ids if i in self._products]

    def get_top_products(self, limit: int = 10) -> List[ProductProfile]:
        return sorted(self._products.values(), key=lambda p: p.score, reverse=True)[:limit]

    def get_high_commission(self, min_rate: float = 20.0) -> List[ProductProfile]:
        return sorted(
            [p for p in self._products.values() if p.commission_rate >= min_rate],
            key=lambda p: p.commission_per_sale, reverse=True,
        )

    def get_recurring_products(self) -> List[ProductProfile]:
        return sorted(
            [p for p in self._products.values() if p.recurring],
            key=lambda p: p.annual_recurring_value, reverse=True,
        )

    def get_seasonal_products(self, month: int = None) -> List[ProductProfile]:
        if month is None:
            month = time.localtime().tm_mon
        return [p for p in self._products.values()
                if p.seasonal and (not p.peak_months or month in p.peak_months)]

    def get_best_sellers(self) -> List[ProductProfile]:
        return sorted(
            [p for p in self._products.values() if p.best_seller_rank > 0],
            key=lambda p: p.best_seller_rank,
        )

    def get_intelligence_report(self) -> Dict[str, Any]:
        products = list(self._products.values())
        return {
            "total_products": len(products),
            "by_category": {c: len(ids) for c, ids in self._category_index.items()},
            "by_program": {c: len(ids) for c, ids in self._program_index.items()},
            "high_commission": len([p for p in products if p.commission_rate >= 20]),
            "recurring": len([p for p in products if p.recurring]),
            "seasonal": len([p for p in products if p.seasonal]),
            "avg_commission_rate": round(
                sum(p.commission_rate for p in products) / len(products), 1
            ) if products else 0,
            "top_products": [p.to_dict() for p in self.get_top_products(5)],
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "products": len(self._products),
            "categories": len(self._category_index),
            "programs": len(self._program_index),
        }


def get_product_intelligence() -> ProductIntelligence:
    return ProductIntelligence()
