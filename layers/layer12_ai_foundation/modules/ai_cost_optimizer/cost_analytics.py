"""CostAnalytics — analyze spending patterns and trends."""
from __future__ import annotations
from typing import Any, Dict, List
from .models import CostEntry

class CostAnalytics:
    def __init__(self) -> None:
        self._entries: List[CostEntry] = []
    def add_entries(self, entries: List[CostEntry]) -> None:
        self._entries.extend(entries)
    def total_cost(self) -> float:
        return sum(e.cost_usd for e in self._entries)
    def cost_by_provider(self) -> Dict[str, float]:
        totals: Dict[str, float] = {}
        for e in self._entries:
            totals[e.provider] = totals.get(e.provider, 0.0) + e.cost_usd
        return totals
    def cost_by_model(self) -> Dict[str, float]:
        totals: Dict[str, float] = {}
        for e in self._entries:
            totals[e.model] = totals.get(e.model, 0.0) + e.cost_usd
        return totals
    def avg_cost_per_request(self) -> float:
        return self.total_cost() / max(len(self._entries), 1)
    def total_tokens(self) -> int:
        return sum(e.total_tokens() for e in self._entries)
    def most_expensive(self, top_n: int = 5) -> List[Dict[str, Any]]:
        sorted_entries = sorted(self._entries, key=lambda e: e.cost_usd, reverse=True)
        return [e.to_dict() for e in sorted_entries[:top_n]]
    def summary(self) -> Dict[str, Any]:
        return {"total_cost": round(self.total_cost(), 6), "total_tokens": self.total_tokens(),
                "request_count": len(self._entries), "avg_per_request": round(self.avg_cost_per_request(), 6)}
