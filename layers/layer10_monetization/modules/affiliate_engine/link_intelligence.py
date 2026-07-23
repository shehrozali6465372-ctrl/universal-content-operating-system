"""LinkIntelligence — Smart link generation, rotation, cloaking, and tracking."""
from __future__ import annotations
import hashlib
import random
import threading
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple


class LinkVariant:
    __slots__ = ("id", "url", "weight", "clicks", "conversions", "revenue", "active")

    def __init__(self, url: str, weight: int = 1) -> None:
        self.id = str(uuid.uuid4())[:8]
        self.url = url
        self.weight = weight
        self.clicks = 0
        self.conversions = 0
        self.revenue = 0.0
        self.active = True

    @property
    def conversion_rate(self) -> float:
        return (self.conversions / self.clicks * 100) if self.clicks > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "url": self.url, "weight": self.weight,
            "clicks": self.clicks, "conversions": self.conversions,
            "revenue": round(self.revenue, 2),
            "conversion_rate": round(self.conversion_rate, 2),
            "active": self.active,
        }


class TrackedLink:
    __slots__ = ("id", "short_slug", "original_url", "cloaked_url", "variants",
                 "niche", "category", "tags", "created_at", "total_clicks",
                 "total_conversions", "total_revenue", "rotation_strategy",
                 "ab_test_enabled")

    def __init__(self, original_url: str, niche: str = "", category: str = "") -> None:
        self.id = str(uuid.uuid4())[:12]
        self.short_slug = hashlib.sha256(original_url.encode()).hexdigest()[:8]
        self.original_url = original_url
        self.cloaked_url = f"/go/{self.short_slug}"
        self.variants: List[LinkVariant] = [LinkVariant(original_url)]
        self.niche = niche
        self.category = category
        self.tags: List[str] = []
        self.created_at = time.time()
        self.total_clicks = 0
        self.total_conversions = 0
        self.total_revenue = 0.0
        self.rotation_strategy = "weighted"
        self.ab_test_enabled = False

    def add_variant(self, url: str, weight: int = 1) -> LinkVariant:
        v = LinkVariant(url, weight)
        self.variants.append(v)
        self.ab_test_enabled = len(self.variants) > 1
        return v

    def get_best_variant(self) -> Optional[LinkVariant]:
        active = [v for v in self.variants if v.active]
        if not active:
            return None
        if self.rotation_strategy == "weighted":
            return self._weighted_choice(active)
        elif self.rotation_strategy == "best_performer":
            return max(active, key=lambda v: v.conversion_rate)
        elif self.rotation_strategy == "round_robin":
            return min(active, key=lambda v: v.clicks)
        return active[0]

    def _weighted_choice(self, variants: List[LinkVariant]) -> LinkVariant:
        total = sum(v.weight for v in variants)
        if total == 0:
            return variants[0]
        r = random.uniform(0, total)
        cumulative = 0
        for v in variants:
            cumulative += v.weight
            if r <= cumulative:
                return v
        return variants[-1]

    def record_click(self) -> LinkVariant:
        v = self.get_best_variant()
        if v:
            v.clicks += 1
            self.total_clicks += 1
        return v

    def record_conversion(self, revenue: float = 0.0) -> Optional[LinkVariant]:
        active = [v for v in self.variants if v.active and v.clicks > 0]
        if not active:
            return None
        best = max(active, key=lambda v: v.conversion_rate)
        best.conversions += 1
        best.revenue += revenue
        self.total_conversions += 1
        self.total_revenue += revenue
        return best

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "short_slug": self.short_slug,
            "original_url": self.original_url,
            "cloaked_url": self.cloaked_url,
            "niche": self.niche,
            "category": self.category,
            "variants": len(self.variants),
            "total_clicks": self.total_clicks,
            "total_conversions": self.total_conversions,
            "total_revenue": round(self.total_revenue, 2),
            "conversion_rate": round(
                (self.total_conversions / self.total_clicks * 100)
                if self.total_clicks > 0 else 0, 2
            ),
            "rotation": self.rotation_strategy,
            "ab_test": self.ab_test_enabled,
        }


class LinkIntelligence:
    """Smart link management with rotation, A/B testing, cloaking, and analytics."""
    _instance: Optional["LinkIntelligence"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "LinkIntelligence":
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
        self._links: Dict[str, TrackedLink] = {}
        self._slug_index: Dict[str, str] = {}
        self._click_stream: List[Dict[str, Any]] = []
        self._niche_index: Dict[str, List[str]] = {}

    def create_link(self, url: str, niche: str = "", category: str = "",
                    tags: List[str] = None, rotation: str = "weighted") -> TrackedLink:
        link = TrackedLink(url, niche, category)
        link.rotation_strategy = rotation
        if tags:
            link.tags = tags
        self._links[link.id] = link
        self._slug_index[link.short_slug] = link.id
        if niche:
            self._niche_index.setdefault(niche, []).append(link.id)
        return link

    def get_link(self, link_id: str) -> Optional[TrackedLink]:
        return self._links.get(link_id)

    def get_by_slug(self, slug: str) -> Optional[TrackedLink]:
        lid = self._slug_index.get(slug)
        return self._links.get(lid) if lid else None

    def resolve_link(self, slug: str) -> Optional[str]:
        link = self.get_by_slug(slug)
        if not link:
            return None
        variant = link.record_click()
        self._click_stream.append({
            "slug": slug, "link_id": link.id,
            "variant_id": variant.id if variant else None,
            "timestamp": time.time(),
        })
        return variant.url if variant else link.original_url

    def add_variant(self, link_id: str, url: str, weight: int = 1) -> Optional[LinkVariant]:
        link = self._links.get(link_id)
        return link.add_variant(url, weight) if link else None

    def get_links_by_niche(self, niche: str) -> List[TrackedLink]:
        ids = self._niche_index.get(niche, [])
        return [self._links[i] for i in ids if i in self._links]

    def get_top_links(self, metric: str = "revenue", limit: int = 10) -> List[TrackedLink]:
        links = list(self._links.values())
        if metric == "revenue":
            links.sort(key=lambda l: l.total_revenue, reverse=True)
        elif metric == "clicks":
            links.sort(key=lambda l: l.total_clicks, reverse=True)
        elif metric == "conversions":
            links.sort(key=lambda l: l.total_conversions, reverse=True)
        elif metric == "conversion_rate":
            links.sort(
                key=lambda l: (l.total_conversions / l.total_clicks if l.total_clicks > 0 else 0),
                reverse=True,
            )
        return links[:limit]

    def get_link_stats(self) -> Dict[str, Any]:
        links = list(self._links.values())
        total_clicks = sum(l.total_clicks for l in links)
        total_conversions = sum(l.total_conversions for l in links)
        total_revenue = sum(l.total_revenue for l in links)
        return {
            "total_links": len(links),
            "active_links": sum(1 for l in links if any(v.active for v in l.variants)),
            "ab_test_links": sum(1 for l in links if l.ab_test_enabled),
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "total_revenue": round(total_revenue, 2),
            "overall_conversion_rate": round(
                (total_conversions / total_clicks * 100) if total_clicks > 0 else 0, 2
            ),
            "click_events": len(self._click_stream),
            "niches": {n: len(ids) for n, ids in self._niche_index.items()},
        }


def get_link_intelligence() -> LinkIntelligence:
    return LinkIntelligence()
