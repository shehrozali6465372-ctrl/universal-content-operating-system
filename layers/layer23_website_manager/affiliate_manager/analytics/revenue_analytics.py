"""RevenueAnalytics — Dashboard for revenue, best products, categories, networks, merchants."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.affiliate_manager.models.affiliate_models import (
    AffiliateProduct, AffiliateClick, Merchant, AffiliateNetwork,
)


class RevenueAnalytics:
    """Generate revenue reports and analytics dashboards."""

    def __init__(self) -> None:
        self._report_log: List[dict] = []

    def generate_dashboard(self, products: List[AffiliateProduct],
                            merchants: List[Merchant],
                            networks: List[AffiliateNetwork],
                            clicks_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a complete revenue dashboard."""
        total_revenue = sum(p.total_commission for p in products)
        total_clicks = sum(p.total_clicks for p in products)
        total_sales = sum(p.total_sales for p in products)
        total_products = len(products)
        active_merchants = len([m for m in merchants if m.status.value == "active"])
        active_networks = len([n for n in networks if n.is_active])

        # Best products by revenue
        best_products = sorted(products, key=lambda p: p.total_commission, reverse=True)[:5]

        # Best categories
        by_category: Dict[str, Dict[str, float]] = {}
        for p in products:
            if p.category not in by_category:
                by_category[p.category] = {"revenue": 0.0, "clicks": 0, "sales": 0}
            by_category[p.category]["revenue"] += p.total_commission
            by_category[p.category]["clicks"] += p.total_clicks
            by_category[p.category]["sales"] += p.total_sales

        # Best networks
        by_network: Dict[str, float] = {}
        for n in networks:
            by_network[n.network_name] = n.total_earnings

        dashboard = {
            "summary": {
                "total_revenue": round(total_revenue, 2),
                "total_clicks": total_clicks,
                "total_sales": total_sales,
                "total_products": total_products,
                "active_merchants": active_merchants,
                "active_networks": active_networks,
                "avg_commission_per_sale": round(total_revenue / max(total_sales, 1), 2),
                "overall_conversion_rate": round((total_sales / max(total_clicks, 1)) * 100, 2),
            },
            "top_products": [
                {"name": p.product_name, "revenue": round(p.total_commission, 2),
                 "clicks": p.total_clicks, "sales": p.total_sales}
                for p in best_products
            ],
            "by_category": {
                cat: {
                    "revenue": round(data["revenue"], 2),
                    "clicks": data["clicks"],
                    "sales": data["sales"],
                }
                for cat, data in sorted(by_category.items(), key=lambda x: x[1]["revenue"], reverse=True)
            },
            "by_network": {name: round(earnings, 2) for name, earnings in
                          sorted(by_network.items(), key=lambda x: x[1], reverse=True)},
        }

        self._report_log.append(dashboard)
        return dashboard

    def get_stats(self) -> Dict[str, Any]:
        return {"total_reports": len(self._report_log)}
