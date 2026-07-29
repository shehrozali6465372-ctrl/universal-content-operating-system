"""Traffic data models — sources, visitors, analytics, campaigns, alerts, forecasts."""
from __future__ import annotations
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


class TrafficSourceType(str, Enum):
    PINTEREST = "pinterest"
    GOOGLE_ORGANIC = "google_organic"
    GOOGLE_DISCOVER = "google_discover"
    BING = "bing"
    DIRECT = "direct"
    REFERRAL = "referral"
    SOCIAL = "social"
    EMAIL = "email"
    OTHER = "other"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class CampaignStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    DRAFT = "draft"


@dataclass
class TrafficSource:
    """Record of a single traffic source visit."""
    source_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    visitor_id: str = ""
    source_type: TrafficSourceType = TrafficSourceType.OTHER
    medium: str = ""
    campaign: str = ""
    article_id: str = ""
    pin_id: str = ""
    board_id: str = ""
    referrer_url: str = ""
    landing_url: str = ""
    country: str = ""
    device: str = "desktop"
    created_at: float = field(default_factory=time.time)
    def to_dict(self) -> Dict[str, Any]:
        return {"source_id": self.source_id, "source": self.source_type.value, "medium": self.medium, "article_id": self.article_id, "pin_id": self.pin_id, "country": self.country, "device": self.device}


@dataclass
class Visitor:
    """Visitor session data."""
    visitor_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    is_new: bool = True
    page_views: int = 1
    session_duration: float = 0.0
    scroll_depth: float = 0.0
    device: str = "desktop"
    browser: str = ""
    country: str = ""
    referrer: str = ""
    first_visit: float = field(default_factory=time.time)
    last_visit: float = field(default_factory=time.time)
    def to_dict(self) -> Dict[str, Any]:
        return {"visitor_id": self.visitor_id, "is_new": self.is_new, "page_views": self.page_views, "session_duration": round(self.session_duration, 1), "device": self.device, "country": self.country}


@dataclass
class TrafficAnalytics:
    """Aggregated traffic analytics for an article/pin."""
    analytics_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    article_id: str = ""
    date: float = field(default_factory=time.time)
    sessions: int = 0
    pageviews: int = 0
    users: int = 0
    new_users: int = 0
    bounce_rate: float = 0.0
    avg_session_duration: float = 0.0
    traffic_source: str = "all"
    pinterest_clicks: int = 0
    pinterest_saves: int = 0
    google_clicks: int = 0
    google_impressions: int = 0
    def to_dict(self) -> Dict[str, Any]:
        return {"article_id": self.article_id, "sessions": self.sessions, "pageviews": self.pageviews, "users": self.users, "bounce_rate": round(self.bounce_rate, 1), "avg_session": round(self.avg_session_duration, 1), "pinterest_clicks": self.pinterest_clicks, "google_clicks": self.google_clicks}


@dataclass
class LandingPage:
    """Landing page performance data."""
    page_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    url: str = ""
    article_id: str = ""
    title: str = ""
    sessions: int = 0
    pageviews: int = 0
    bounce_rate: float = 0.0
    avg_duration: float = 0.0
    exits: int = 0
    top_source: str = ""
    created_at: float = field(default_factory=time.time)
    def to_dict(self) -> Dict[str, Any]:
        return {"url": self.url, "title": self.title[:50], "sessions": self.sessions, "bounce_rate": round(self.bounce_rate, 1), "top_source": self.top_source}


@dataclass
class Campaign:
    """Traffic campaign data."""
    campaign_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = ""
    campaign_type: str = "seasonal"
    status: CampaignStatus = CampaignStatus.DRAFT
    source_type: TrafficSourceType = TrafficSourceType.PINTEREST
    budget: float = 0.0
    spent: float = 0.0
    clicks: int = 0
    impressions: int = 0
    conversions: int = 0
    start_date: float = 0.0
    end_date: float = 0.0
    niche: str = ""
    created_at: float = field(default_factory=time.time)
    @property
    def ctr(self) -> float:
        return round((self.clicks / max(self.impressions, 1)) * 100, 2)
    @property
    def conversion_rate(self) -> float:
        return round((self.conversions / max(self.clicks, 1)) * 100, 2)
    @property
    def roi(self) -> float:
        return round(((self.conversions * 10) - self.spent) / max(self.spent, 1) * 100, 2)
    def to_dict(self) -> Dict[str, Any]:
        return {"campaign_id": self.campaign_id, "name": self.name, "status": self.status.value, "clicks": self.clicks, "impressions": self.impressions, "ctr": self.ctr, "conversion_rate": self.conversion_rate, "roi": self.roi}


@dataclass
class Alert:
    """Traffic alert/notification."""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    severity: AlertSeverity = AlertSeverity.INFO
    title: str = ""
    message: str = ""
    source_type: str = ""
    article_id: str = ""
    metric_value: float = 0.0
    threshold: float = 0.0
    is_read: bool = False
    created_at: float = field(default_factory=time.time)
    def to_dict(self) -> Dict[str, Any]:
        return {"alert_id": self.alert_id, "severity": self.severity.value, "title": self.title, "message": self.message[:80], "is_read": self.is_read}


@dataclass
class TrafficForecast:
    """Traffic prediction data."""
    forecast_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    period: str = "daily"
    predicted_visitors: int = 0
    predicted_pageviews: int = 0
    confidence: float = 0.0
    forecast_date: float = field(default_factory=time.time)
    factors: List[str] = field(default_factory=list)
    def to_dict(self) -> Dict[str, Any]:
        return {"period": self.period, "predicted_visitors": self.predicted_visitors, "predicted_pageviews": self.predicted_pageviews, "confidence": round(self.confidence, 2)}
