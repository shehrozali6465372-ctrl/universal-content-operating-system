"""RevenueSourceManager — Manage all revenue sources: Amazon, Impact, CJ, ShareASale, etc."""
from __future__ import annotations
import time, threading
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.revenue_manager.models.revenue_models import RevenueSource


class RevenueSourceManager:
    PRESETS = [
        {"name": "Amazon Associates", "network": "Amazon", "commission": 6.0},
        {"name": "Impact", "network": "Impact", "commission": 8.0},
        {"name": "CJ Affiliate", "network": "CJ", "commission": 7.0},
        {"name": "ShareASale", "network": "ShareASale", "commission": 6.0},
        {"name": "Awin", "network": "Awin", "commission": 7.0},
        {"name": "Rakuten", "network": "Rakuten", "commission": 5.0},
        {"name": "ClickBank", "network": "ClickBank", "commission": 50.0},
        {"name": "Digistore24", "network": "Digistore24", "commission": 40.0},
    ]

    def __init__(self):
        self._sources: Dict[str, RevenueSource] = {}
        self._lock = threading.Lock()

    def register_source(self, name: str, network: str = "", commission_rate: float = 0.0) -> RevenueSource:
        src = RevenueSource(name=name, network=network, commission_rate=commission_rate)
        with self._lock: self._sources[src.source_id] = src
        return src

    def load_presets(self) -> List[RevenueSource]:
        return [self.register_source(p["name"], p["network"], p["commission"]) for p in self.PRESETS]

    def get_source(self, source_id: str) -> Optional[RevenueSource]:
        return self._sources.get(source_id)

    def get_all_sources(self) -> List[RevenueSource]:
        return list(self._sources.values())

    def record_revenue(self, source_id: str, amount: float, commission: float):
        src = self._sources.get(source_id)
        if src:
            with self._lock: src.total_revenue += amount; src.total_commission += commission; src.transaction_count += 1

    def get_top_sources(self, top_k: int = 5) -> List[RevenueSource]:
        return sorted(self._sources.values(), key=lambda s: s.total_revenue, reverse=True)[:top_k]

    def get_stats(self) -> Dict:
        return {"total_sources": len(self._sources), "total_revenue": round(sum(s.total_revenue for s in self._sources.values()), 2), "total_commission": round(sum(s.total_commission for s in self._sources.values()), 2)}
