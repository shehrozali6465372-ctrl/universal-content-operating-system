"""ProductRevenueAnalyzer — Analyze best/worst products, highest EPC, highest commission."""
from __future__ import annotations
import time, threading
from typing import Any, Dict, List, Optional


class ProductRevenueAnalyzer:
    def __init__(self):
        self._products: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    def record_product(self, product_id: str, product_name: str = "", merchant: str = "",
                        sales: int = 0, revenue: float = 0.0, commission: float = 0.0, clicks: int = 0):
        with self._lock:
            if product_id not in self._products:
                self._products[product_id] = {"product_id": product_id, "product_name": product_name,
                    "merchant": merchant, "sales": 0, "revenue": 0.0, "commission": 0.0, "clicks": 0}
            p = self._products[product_id]
            p["sales"] += sales; p["revenue"] += revenue; p["commission"] += commission; p["clicks"] += clicks

    def get_best_products(self, top_k: int = 5) -> List[Dict]:
        return sorted(self._products.values(), key=lambda p: p["revenue"], reverse=True)[:top_k]

    def get_highest_epc(self, top_k: int = 5) -> List[Dict]:
        scored = []
        for p in self._products.values():
            epc = p["commission"] / max(p["clicks"], 1)
            scored.append({**p, "epc": round(epc, 4)})
        return sorted(scored, key=lambda x: x["epc"], reverse=True)[:top_k]

    def get_summary(self) -> Dict:
        prods = list(self._products.values())
        return {"total_products": len(prods), "total_revenue": round(sum(p["revenue"] for p in prods), 2),
                "total_commission": round(sum(p["commission"] for p in prods), 2), "total_sales": sum(p["sales"] for p in prods)}

    def get_stats(self) -> Dict: return {"total_products": len(self._products)}
