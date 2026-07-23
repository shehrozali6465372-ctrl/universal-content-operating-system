"""RevenueAnalytics — Tracks clicks, sales, EPC, conversion rates, and revenue per post."""
from __future__ import annotations
import threading
import time
from typing import Any, Dict, List, Optional


class RevenueEvent:
    __slots__ = ("id", "event_type", "post_id", "link_id", "program_id",
                 "niche", "platform", "amount", "commission", "currency",
                 "metadata", "timestamp")

    def __init__(self, event_type: str, post_id: str = "", link_id: str = "",
                 program_id: str = "", amount: float = 0.0, commission: float = 0.0,
                 niche: str = "", platform: str = "", currency: str = "USD") -> None:
        self.id = f"evt_{int(time.time() * 1000)}"
        self.event_type = event_type
        self.post_id = post_id
        self.link_id = link_id
        self.program_id = program_id
        self.niche = niche
        self.platform = platform
        self.amount = amount
        self.commission = commission
        self.currency = currency
        self.metadata: Dict[str, Any] = {}
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "type": self.event_type, "post_id": self.post_id,
            "link_id": self.link_id, "program_id": self.program_id,
            "niche": self.niche, "platform": self.platform,
            "amount": round(self.amount, 2),
            "commission": round(self.commission, 2),
            "currency": self.currency, "timestamp": self.timestamp,
        }


class PostRevenue:
    __slots__ = ("post_id", "title", "niche", "platform", "clicks", "impressions",
                 "conversions", "revenue", "commission", "first_click", "last_click")

    def __init__(self, post_id: str, title: str = "", niche: str = "",
                 platform: str = "") -> None:
        self.post_id = post_id
        self.title = title
        self.niche = niche
        self.platform = platform
        self.clicks = 0
        self.impressions = 0
        self.conversions = 0
        self.revenue = 0.0
        self.commission = 0.0
        self.first_click = 0.0
        self.last_click = 0.0

    @property
    def ctr(self) -> float:
        return (self.clicks / self.impressions * 100) if self.impressions > 0 else 0.0

    @property
    def conversion_rate(self) -> float:
        return (self.conversions / self.clicks * 100) if self.clicks > 0 else 0.0

    @property
    def epc(self) -> float:
        return (self.revenue / self.clicks) if self.clicks > 0 else 0.0

    @property
    def rpm(self) -> float:
        return (self.revenue / self.impressions * 1000) if self.impressions > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "post_id": self.post_id, "title": self.title,
            "niche": self.niche, "platform": self.platform,
            "clicks": self.clicks, "impressions": self.impressions,
            "conversions": self.conversions,
            "revenue": round(self.revenue, 2),
            "commission": round(self.commission, 2),
            "ctr": round(self.ctr, 2),
            "conversion_rate": round(self.conversion_rate, 2),
            "epc": round(self.epc, 4),
            "rpm": round(self.rpm, 2),
        }


class NicheRevenue:
    __slots__ = ("niche", "posts", "total_clicks", "total_impressions",
                 "total_conversions", "total_revenue", "total_commission")

    def __init__(self, niche: str) -> None:
        self.niche = niche
        self.posts: Dict[str, PostRevenue] = {}
        self.total_clicks = 0
        self.total_impressions = 0
        self.total_conversions = 0
        self.total_revenue = 0.0
        self.total_commission = 0.0

    @property
    def conversion_rate(self) -> float:
        return (self.total_conversions / self.total_clicks * 100) if self.total_clicks > 0 else 0.0

    @property
    def epc(self) -> float:
        return (self.total_revenue / self.total_clicks) if self.total_clicks > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "niche": self.niche, "total_posts": len(self.posts),
            "total_clicks": self.total_clicks,
            "total_impressions": self.total_impressions,
            "total_conversions": self.total_conversions,
            "total_revenue": round(self.total_revenue, 2),
            "total_commission": round(self.total_commission, 2),
            "conversion_rate": round(self.conversion_rate, 2),
            "epc": round(self.epc, 4),
        }


class RevenueAnalytics:
    """Tracks and analyzes revenue across posts, niches, platforms, and time periods."""
    _instance: Optional["RevenueAnalytics"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "RevenueAnalytics":
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
        self._events: List[RevenueEvent] = []
        self._posts: Dict[str, PostRevenue] = {}
        self._niches: Dict[str, NicheRevenue] = {}
        self._daily: Dict[str, Dict[str, float]] = {}

    def record_click(self, post_id: str, link_id: str = "", program_id: str = "",
                     niche: str = "", platform: str = "") -> RevenueEvent:
        evt = RevenueEvent("click", post_id, link_id, program_id,
                           niche=niche, platform=platform)
        self._events.append(evt)
        self._update_post(post_id, "click", niche=niche, platform=platform)
        self._update_niche(niche, "click")
        self._update_daily("clicks", 1)
        return evt

    def record_impression(self, post_id: str, niche: str = "", platform: str = "") -> RevenueEvent:
        evt = RevenueEvent("impression", post_id, niche=niche, platform=platform)
        self._events.append(evt)
        self._update_post(post_id, "impression", niche=niche, platform=platform)
        self._update_niche(niche, "impression")
        self._update_daily("impressions", 1)
        return evt

    def record_conversion(self, post_id: str, amount: float, commission: float = 0.0,
                          link_id: str = "", program_id: str = "", niche: str = "",
                          platform: str = "") -> RevenueEvent:
        evt = RevenueEvent("conversion", post_id, link_id, program_id,
                           amount=amount, commission=commission,
                           niche=niche, platform=platform)
        self._events.append(evt)
        self._update_post(post_id, "conversion", amount=amount,
                          commission=commission, niche=niche, platform=platform)
        self._update_niche(niche, "conversion", amount=amount, commission=commission)
        self._update_daily("revenue", amount)
        return evt

    def _update_post(self, post_id: str, event_type: str, **kwargs) -> None:
        if post_id not in self._posts:
            self._posts[post_id] = PostRevenue(
                post_id, niche=kwargs.get("niche", ""),
                platform=kwargs.get("platform", ""),
            )
        post = self._posts[post_id]
        now = time.time()
        if event_type == "click":
            post.clicks += 1
            if post.first_click == 0:
                post.first_click = now
            post.last_click = now
        elif event_type == "impression":
            post.impressions += 1
        elif event_type == "conversion":
            post.conversions += 1
            post.revenue += kwargs.get("amount", 0)
            post.commission += kwargs.get("commission", 0)

    def _update_niche(self, niche: str, event_type: str, **kwargs) -> None:
        if not niche:
            return
        if niche not in self._niches:
            self._niches[niche] = NicheRevenue(niche)
        nr = self._niches[niche]
        if event_type == "click":
            nr.total_clicks += 1
        elif event_type == "impression":
            nr.total_impressions += 1
        elif event_type == "conversion":
            nr.total_conversions += 1
            nr.total_revenue += kwargs.get("amount", 0)
            nr.total_commission += kwargs.get("commission", 0)

    def _update_daily(self, metric: str, value: float) -> None:
        day = time.strftime("%Y-%m-%d")
        self._daily.setdefault(day, {})
        self._daily[day][metric] = self._daily[day].get(metric, 0) + value

    def get_post_revenue(self, post_id: str) -> Optional[PostRevenue]:
        return self._posts.get(post_id)

    def get_top_posts(self, metric: str = "revenue", limit: int = 10) -> List[PostRevenue]:
        posts = list(self._posts.values())
        key_map = {
            "revenue": lambda p: p.revenue,
            "clicks": lambda p: p.clicks,
            "conversions": lambda p: p.conversions,
            "conversion_rate": lambda p: p.conversion_rate,
            "epc": lambda p: p.epc,
            "ctr": lambda p: p.ctr,
        }
        fn = key_map.get(metric, key_map["revenue"])
        posts.sort(key=fn, reverse=True)
        return posts[:limit]

    def get_niche_revenue(self) -> List[NicheRevenue]:
        niches = list(self._niches.values())
        niches.sort(key=lambda n: n.total_revenue, reverse=True)
        return niches

    def get_daily_revenue(self, days: int = 30) -> Dict[str, Dict[str, float]]:
        sorted_days = sorted(self._daily.keys(), reverse=True)[:days]
        return {d: self._daily[d] for d in sorted_days}

    def get_analytics_summary(self) -> Dict[str, Any]:
        total_clicks = sum(e.event_type == "click" for e in self._events)
        total_impressions = sum(e.event_type == "impression" for e in self._events)
        total_conversions = sum(e.event_type == "conversion" for e in self._events)
        total_revenue = sum(e.amount for e in self._events if e.event_type == "conversion")
        total_commission = sum(e.commission for e in self._events if e.event_type == "conversion")
        return {
            "total_events": len(self._events),
            "total_clicks": total_clicks,
            "total_impressions": total_impressions,
            "total_conversions": total_conversions,
            "total_revenue": round(total_revenue, 2),
            "total_commission": round(total_commission, 2),
            "overall_ctr": round(
                (total_clicks / total_impressions * 100) if total_impressions > 0 else 0, 2
            ),
            "overall_conversion_rate": round(
                (total_conversions / total_clicks * 100) if total_clicks > 0 else 0, 2
            ),
            "overall_epc": round(
                (total_revenue / total_clicks) if total_clicks > 0 else 0, 4
            ),
            "total_posts": len(self._posts),
            "total_niches": len(self._niches),
            "daily_days": len(self._daily),
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "events": len(self._events),
            "posts": len(self._posts),
            "niches": len(self._niches),
            "daily_entries": len(self._daily),
        }


def get_revenue_analytics() -> RevenueAnalytics:
    return RevenueAnalytics()
