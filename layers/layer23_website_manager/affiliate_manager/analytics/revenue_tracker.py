"""RevenueTracker — Track clicks, sales, commissions, EPC, conversion rates, daily/monthly revenue."""
from __future__ import annotations
import time
import threading
import random
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.affiliate_manager.models.affiliate_models import AffiliateClick
from layers.layer23_website_manager.affiliate_manager.exceptions import RevenueTrackingError


class RevenueTracker:
    """Track every affiliate click, sale, commission, and calculate key metrics."""

    def __init__(self) -> None:
        self._clicks: List[AffiliateClick] = []
        self._lock = threading.Lock()

    def record_click(self, product_id: str, article_id: str = "",
                      pin_id: str = "", source: str = "direct") -> AffiliateClick:
        """Record an affiliate link click."""
        click = AffiliateClick(
            product_id=product_id,
            article_id=article_id,
            pin_id=pin_id,
            source=source,
        )
        with self._lock:
            self._clicks.append(click)
        return click

    def record_sale(self, click_id: str, sale_amount: float,
                     commission: float) -> bool:
        """Record a sale conversion for a click."""
        with self._lock:
            for click in self._clicks:
                if click.click_id == click_id:
                    click.converted = True
                    click.sale_amount = sale_amount
                    click.commission = commission
                    return True
        return False

    def get_clicks(self, days: int = 30, source: str = "") -> List[AffiliateClick]:
        """Get clicks within time period."""
        cutoff = time.time() - (days * 86400)
        clicks = [c for c in self._clicks if c.click_time >= cutoff]
        if source:
            clicks = [c for c in clicks if c.source == source]
        return clicks

    def get_revenue_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get revenue statistics for a time period."""
        clicks = self.get_clicks(days)
        total_clicks = len(clicks)
        conversions = [c for c in clicks if c.converted]
        total_sales = len(conversions)
        total_revenue = sum(c.sale_amount for c in conversions)
        total_commission = sum(c.commission for c in conversions)
        conversion_rate = (total_sales / total_clicks * 100) if total_clicks > 0 else 0.0
        epc = (total_commission / total_clicks) if total_clicks > 0 else 0.0

        # By source
        by_source: Dict[str, int] = {}
        for c in clicks:
            by_source[c.source] = by_source.get(c.source, 0) + 1

        return {
            "period_days": days,
            "total_clicks": total_clicks,
            "total_sales": total_sales,
            "total_revenue": round(total_revenue, 2),
            "total_commission": round(total_commission, 2),
            "conversion_rate": round(conversion_rate, 2),
            "epc": round(epc, 4),
            "by_source": by_source,
        }

    def simulate_day(self, product_id: str, avg_clicks: int = 50,
                      conversion_rate: float = 2.0,
                      avg_sale: float = 50.0,
                      commission_rate: float = 6.0) -> Dict[str, Any]:
        """Simulate a day of affiliate activity (for testing)."""
        clicks_today = random.randint(int(avg_clicks * 0.7), int(avg_clicks * 1.3))
        sales_today = int(clicks_today * conversion_rate / 100)
        revenue_today = sales_today * avg_sale
        commission_today = revenue_today * commission_rate / 100

        for _ in range(clicks_today):
            click = self.record_click(product_id, source="pinterest")

        return {
            "clicks": clicks_today,
            "sales": sales_today,
            "revenue": round(revenue_today, 2),
            "commission": round(commission_today, 2),
        }

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._clicks)
        conversions = sum(1 for c in self._clicks if c.converted)
        return {
            "total_clicks": total,
            "total_conversions": conversions,
            "total_revenue": round(sum(c.sale_amount for c in self._clicks if c.converted), 2),
            "total_commission": round(sum(c.commission for c in self._clicks if c.converted), 2),
        }
