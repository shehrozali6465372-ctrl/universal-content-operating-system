"""Analytics data models — summaries, KPIs, insights, trends, reports."""
from __future__ import annotations
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


class KPICategory(str, Enum):
    TRAFFIC = "traffic"
    ENGAGEMENT = "engagement"
    REVENUE = "revenue"
    SEO = "seo"
    CONTENT = "content"
    GROWTH = "growth"


class InsightType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    OPPORTUNITY = "opportunity"
    WARNING = "warning"


@dataclass
class AnalyticsSummary:
    """Daily/weekly/monthly rollup of all analytics data."""
    summary_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    date: float = field(default_factory=time.time)
    period: str = "daily"  # daily, weekly, monthly
    website_views: int = 0
    website_sessions: int = 0
    website_bounce_rate: float = 0.0
    pinterest_impressions: int = 0
    pinterest_clicks: int = 0
    pinterest_saves: int = 0
    organic_clicks: int = 0
    organic_impressions: int = 0
    affiliate_clicks: int = 0
    affiliate_sales: int = 0
    affiliate_commission: float = 0.0
    affiliate_revenue: float = 0.0
    total_articles: int = 0
    total_pins: int = 0
    growth_rate: float = 0.0
    def to_dict(self) -> Dict[str, Any]:
        return {"period": self.period, "website_views": self.website_views, "pinterest_clicks": self.pinterest_clicks, "organic_clicks": self.organic_clicks, "affiliate_sales": self.affiliate_sales, "affiliate_revenue": round(self.affiliate_revenue, 2), "growth_rate": round(self.growth_rate, 1)}


@dataclass
class AnalyticsReport:
    """Generated analytics report metadata."""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    report_type: str = "daily"
    period: str = ""
    generated_at: float = field(default_factory=time.time)
    format: str = "json"
    status: str = "completed"
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebsiteAnalyticsData:
    article_id: str = ""; title: str = ""; views: int = 0; sessions: int = 0
    bounce_rate: float = 0.0; avg_time_on_page: float = 0.0; top_source: str = ""
    def to_dict(self) -> Dict: return {"title": self.title[:40], "views": self.views, "bounce_rate": round(self.bounce_rate, 1), "avg_time": round(self.avg_time_on_page, 1)}

@dataclass
class PinterestAnalyticsData:
    pin_id: str = ""; board_id: str = ""; account_id: str = ""
    impressions: int = 0; saves: int = 0; clicks: int = 0; outbound_clicks: int = 0
    def to_dict(self) -> Dict: return {"impressions": self.impressions, "saves": self.saves, "clicks": self.clicks}

@dataclass
class SEOAnalyticsData:
    article_id: str = ""; keyword: str = ""; position: float = 0.0
    impressions: int = 0; clicks: int = 0; ctr: float = 0.0; is_indexed: bool = False
    def to_dict(self) -> Dict: return {"keyword": self.keyword, "position": round(self.position, 1), "clicks": self.clicks, "ctr": round(self.ctr, 2)}

@dataclass
class AffiliateAnalyticsData:
    product_id: str = ""; product_name: str = ""; clicks: int = 0
    sales: int = 0; commission: float = 0.0; revenue: float = 0.0; epc: float = 0.0
    def to_dict(self) -> Dict: return {"product": self.product_name[:30], "sales": self.sales, "commission": round(self.commission, 2), "epc": round(self.epc, 4)}

@dataclass
class ContentAnalyticsData:
    article_id: str = ""; title: str = ""; total_views: int = 0
    total_pins: int = 0; total_clicks: int = 0; total_revenue: float = 0.0
    is_evergreen: bool = False; trend: str = "stable"
    def to_dict(self) -> Dict: return {"title": self.title[:40], "views": self.total_views, "revenue": round(self.total_revenue, 2), "trend": self.trend}

@dataclass
class CampaignAnalyticsData:
    campaign_id: str = ""; name: str = ""; impressions: int = 0
    clicks: int = 0; conversions: int = 0; spent: float = 0.0
    revenue: float = 0.0; roi: float = 0.0
    def to_dict(self) -> Dict: return {"name": self.name, "clicks": self.clicks, "conversions": self.conversions, "roi": round(self.roi, 1)}

@dataclass
class KPI:
    kpi_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    category: KPICategory = KPICategory.TRAFFIC
    name: str = ""; value: float = 0.0; previous_value: float = 0.0
    unit: str = ""; trend: str = "stable"
    @property
    def change_pct(self) -> float:
        if self.previous_value == 0: return 0.0
        return round(((self.value - self.previous_value) / self.previous_value) * 100, 1)
    def to_dict(self) -> Dict:
        return {"name": self.name, "value": self.value, "unit": self.unit, "change": self.change_pct, "trend": self.trend}

@dataclass
class AIInsight:
    insight_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    insight_type: InsightType = InsightType.OPPORTUNITY
    title: str = ""; message: str = ""; category: str = ""
    metric_value: float = 0.0; recommendation: str = ""
    created_at: float = field(default_factory=time.time)
    def to_dict(self) -> Dict:
        return {"type": self.insight_type.value, "title": self.title, "message": self.message[:100], "recommendation": self.recommendation[:100]}

@dataclass
class TrendData:
    trend_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    category: str = ""; item: str = ""; metric: str = ""
    current_value: float = 0.0; previous_value: float = 0.0
    change_pct: float = 0.0; direction: str = "up"
    def to_dict(self) -> Dict:
        return {"category": self.category, "item": self.item, "change": round(self.change_pct, 1), "direction": self.direction}
