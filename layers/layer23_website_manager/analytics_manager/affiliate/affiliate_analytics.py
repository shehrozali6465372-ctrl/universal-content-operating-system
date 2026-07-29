"""AffiliateAnalytics — Track clicks, sales, conversion rate, commission, EPC, top products."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.analytics_manager.models.analytics_models import AffiliateAnalyticsData


class AffiliateAnalytics:
    def __init__(self):
        self._products: Dict[str, AffiliateAnalyticsData] = {}
        self._lock = threading.Lock()
        self._total_clicks = 0; self._total_sales = 0; self._total_commission = 0.0; self._total_revenue = 0.0

    def record_product(self, product_id: str, product_name: str = "",
                        clicks: int = 0, sales: int = 0, commission: float = 0.0, revenue: float = 0.0):
        with self._lock:
            if product_id not in self._products:
                self._products[product_id] = AffiliateAnalyticsData(product_id=product_id, product_name=product_name)
            p = self._products[product_id]
            p.clicks += clicks; p.sales += sales; p.commission += commission; p.revenue += revenue
            p.epc = p.commission / max(p.clicks, 1)
            self._total_clicks += clicks; self._total_sales += sales
            self._total_commission += commission; self._total_revenue += revenue

    def get_top_products(self, top_k: int = 5) -> List[AffiliateAnalyticsData]:
        return sorted(self._products.values(), key=lambda p: p.revenue, reverse=True)[:top_k]

    def get_summary(self) -> Dict[str, Any]:
        return {"total_products": len(self._products), "total_clicks": self._total_clicks,
                "total_sales": self._total_sales, "total_commission": round(self._total_commission, 2),
                "total_revenue": round(self._total_revenue, 2),
                "conversion_rate": round((self._total_sales / max(self._total_clicks, 1)) * 100, 2),
                "epc": round(self._total_commission / max(self._total_clicks, 1), 4)}

    def get_stats(self) -> Dict:
        s = self.get_summary(); return {"total_products": s["total_products"], "total_revenue": s["total_revenue"]}
