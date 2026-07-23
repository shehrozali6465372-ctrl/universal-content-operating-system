"""AffiliateManager — Manages affiliate programs, IDs, links, and commission tracking."""
from __future__ import annotations
import hashlib
import threading
import time
import uuid
from typing import Any, Dict, List, Optional


class AffiliateProgram:
    __slots__ = ("id", "name", "platform", "base_url", "commission_type",
                 "commission_rate", "cookie_days", "categories", "api_key",
                 "api_secret", "status", "created_at", "total_clicks",
                 "total_conversions", "total_revenue")

    def __init__(self, name: str, platform: str, base_url: str = "",
                 commission_type: str = "percentage", commission_rate: float = 0.0,
                 cookie_days: int = 30, categories: List[str] = None) -> None:
        self.id = str(uuid.uuid4())[:12]
        self.name = name
        self.platform = platform
        self.base_url = base_url
        self.commission_type = commission_type
        self.commission_rate = commission_rate
        self.cookie_days = cookie_days
        self.categories = categories or []
        self.api_key = ""
        self.api_secret = ""
        self.status = "active"
        self.created_at = time.time()
        self.total_clicks = 0
        self.total_conversions = 0
        self.total_revenue = 0.0

    @property
    def conversion_rate(self) -> float:
        if self.total_clicks == 0:
            return 0.0
        return (self.total_conversions / self.total_clicks) * 100

    @property
    def epc(self) -> float:
        if self.total_clicks == 0:
            return 0.0
        return self.total_revenue / self.total_clicks

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "platform": self.platform,
            "base_url": self.base_url,
            "commission_type": self.commission_type,
            "commission_rate": self.commission_rate,
            "cookie_days": self.cookie_days,
            "categories": self.categories,
            "status": self.status,
            "total_clicks": self.total_clicks,
            "total_conversions": self.total_conversions,
            "total_revenue": round(self.total_revenue, 2),
            "conversion_rate": round(self.conversion_rate, 2),
            "epc": round(self.epc, 4),
        }


class AffiliateLink:
    __slots__ = ("id", "program_id", "product_url", "affiliate_url",
                 "tracking_id", "niche", "category", "clicks", "conversions",
                 "revenue", "created_at", "last_clicked", "status")

    def __init__(self, program_id: str, product_url: str, affiliate_url: str,
                 tracking_id: str = "", niche: str = "", category: str = "") -> None:
        self.id = str(uuid.uuid4())[:12]
        self.program_id = program_id
        self.product_url = product_url
        self.affiliate_url = affiliate_url
        self.tracking_id = tracking_id or self.id
        self.niche = niche
        self.category = category
        self.clicks = 0
        self.conversions = 0
        self.revenue = 0.0
        self.created_at = time.time()
        self.last_clicked = 0.0
        self.status = "active"

    @property
    def conversion_rate(self) -> float:
        return (self.conversions / self.clicks * 100) if self.clicks > 0 else 0.0

    @property
    def epc(self) -> float:
        return (self.revenue / self.clicks) if self.clicks > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "program_id": self.program_id,
            "product_url": self.product_url,
            "affiliate_url": self.affiliate_url,
            "tracking_id": self.tracking_id,
            "niche": self.niche,
            "category": self.category,
            "clicks": self.clicks,
            "conversions": self.conversions,
            "revenue": round(self.revenue, 2),
            "conversion_rate": round(self.conversion_rate, 2),
            "epc": round(self.epc, 4),
            "status": self.status,
        }


class AffiliateManager:
    """Manages affiliate programs, links, tracking, and commission data."""
    _instance: Optional["AffiliateManager"] = None
    _lock = threading.Lock()

    PRESET_PROGRAMS = {
        "amazon": {
            "name": "Amazon Associates",
            "platform": "amazon",
            "base_url": "https://www.amazon.com",
            "commission_type": "percentage",
            "commission_rate": 4.0,
            "cookie_days": 24,
            "categories": ["electronics", "books", "home", "fashion", "sports"],
        },
        "shopify": {
            "name": "Shopify Affiliate",
            "platform": "shopify",
            "base_url": "https://www.shopify.com",
            "commission_type": "fixed",
            "commission_rate": 58.0,
            "cookie_days": 30,
            "categories": ["ecommerce", "saas", "business"],
        },
        "binance": {
            "name": "Binance Affiliate",
            "platform": "binance",
            "base_url": "https://www.binance.com",
            "commission_type": "percentage",
            "commission_rate": 20.0,
            "cookie_days": 90,
            "categories": ["crypto", "trading", "finance"],
        },
        "clickbank": {
            "name": "ClickBank",
            "platform": "clickbank",
            "base_url": "https://www.clickbank.com",
            "commission_type": "percentage",
            "commission_rate": 50.0,
            "cookie_days": 60,
            "categories": ["health", "fitness", "self-help", "digital"],
        },
        "shareasale": {
            "name": "ShareASale",
            "platform": "shareasale",
            "base_url": "https://www.shareasale.com",
            "commission_type": "percentage",
            "commission_rate": 10.0,
            "cookie_days": 30,
            "categories": ["fashion", "home", "beauty", "tech"],
        },
        "cj_affiliate": {
            "name": "CJ Affiliate",
            "platform": "cj",
            "base_url": "https://www.cj.com",
            "commission_type": "percentage",
            "commission_rate": 8.0,
            "cookie_days": 45,
            "categories": ["retail", "travel", "finance", "tech"],
        },
    }

    def __new__(cls) -> "AffiliateManager":
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
        self._programs: Dict[str, AffiliateProgram] = {}
        self._links: Dict[str, AffiliateLink] = {}
        self._tracking_index: Dict[str, List[str]] = {}
        self._click_log: List[Dict[str, Any]] = []
        self._conversion_log: List[Dict[str, Any]] = []
        self._register_presets()

    def _register_presets(self) -> None:
        for key, preset in self.PRESET_PROGRAMS.items():
            prog = AffiliateProgram(**preset)
            self._programs[key] = prog

    def add_program(self, name: str, platform: str, base_url: str = "",
                    commission_type: str = "percentage", commission_rate: float = 0.0,
                    cookie_days: int = 30, categories: List[str] = None,
                    api_key: str = "", api_secret: str = "") -> AffiliateProgram:
        prog = AffiliateProgram(name, platform, base_url, commission_type,
                                commission_rate, cookie_days, categories or [])
        prog.api_key = api_key
        prog.api_secret = api_secret
        key = platform.lower().replace(" ", "_")
        self._programs[key] = prog
        return prog

    def get_program(self, key: str) -> Optional[AffiliateProgram]:
        return self._programs.get(key)

    def list_programs(self) -> List[AffiliateProgram]:
        return list(self._programs.values())

    def add_link(self, program_id: str, product_url: str, affiliate_url: str,
                 tracking_id: str = "", niche: str = "", category: str = "") -> AffiliateLink:
        link = AffiliateLink(program_id, product_url, affiliate_url,
                             tracking_id, niche, category)
        self._links[link.id] = link

        if tracking_id:
            self._tracking_index.setdefault(tracking_id, []).append(link.id)
        return link

    def get_link(self, link_id: str) -> Optional[AffiliateLink]:
        return self._links.get(link_id)

    def get_links_by_niche(self, niche: str) -> List[AffiliateLink]:
        return [l for l in self._links.values() if l.niche == niche and l.status == "active"]

    def get_links_by_program(self, program_id: str) -> List[AffiliateLink]:
        return [l for l in self._links.values() if l.program_id == program_id]

    def get_links_by_category(self, category: str) -> List[AffiliateLink]:
        return [l for l in self._links.values() if l.category == category and l.status == "active"]

    def record_click(self, link_id: str, source: str = "",
                     platform: str = "") -> Optional[Dict[str, Any]]:
        link = self._links.get(link_id)
        if not link:
            return None
        link.clicks += 1
        link.last_clicked = time.time()

        prog = self._programs.get(link.program_id)
        if prog:
            prog.total_clicks += 1

        event = {
            "link_id": link_id,
            "program_id": link.program_id,
            "niche": link.niche,
            "source": source,
            "platform": platform,
            "timestamp": time.time(),
        }
        self._click_log.append(event)
        return event

    def record_conversion(self, link_id: str, revenue: float = 0.0,
                          source: str = "") -> Optional[Dict[str, Any]]:
        link = self._links.get(link_id)
        if not link:
            return None
        link.conversions += 1
        link.revenue += revenue

        prog = self._programs.get(link.program_id)
        if prog:
            prog.total_conversions += 1
            prog.total_revenue += revenue

        event = {
            "link_id": link_id,
            "program_id": link.program_id,
            "revenue": revenue,
            "source": source,
            "timestamp": time.time(),
        }
        self._conversion_log.append(event)
        return event

    def get_revenue_summary(self) -> Dict[str, Any]:
        total_clicks = sum(p.total_clicks for p in self._programs.values())
        total_conversions = sum(p.total_conversions for p in self._programs.values())
        total_revenue = sum(p.total_revenue for p in self._programs.values())
        return {
            "total_programs": len(self._programs),
            "active_programs": sum(1 for p in self._programs.values() if p.status == "active"),
            "total_links": len(self._links),
            "active_links": sum(1 for l in self._links.values() if l.status == "active"),
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "total_revenue": round(total_revenue, 2),
            "overall_conversion_rate": round(
                (total_conversions / total_clicks * 100) if total_clicks > 0 else 0, 2
            ),
            "overall_epc": round(
                (total_revenue / total_clicks) if total_clicks > 0 else 0, 4
            ),
            "programs": {k: p.to_dict() for k, p in self._programs.items()},
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "programs": len(self._programs),
            "links": len(self._links),
            "clicks_logged": len(self._click_log),
            "conversions_logged": len(self._conversion_log),
        }


def get_affiliate_manager() -> AffiliateManager:
    return AffiliateManager()
