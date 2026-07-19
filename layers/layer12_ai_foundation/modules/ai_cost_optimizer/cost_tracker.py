"""CostTracker — track all AI API costs in real-time."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional
from .models import CostEntry

class CostTracker:
    def __init__(self, daily_budget: float = 10.0) -> None:
        self.daily_budget = daily_budget
        self._entries: List[CostEntry] = []
        self._daily_totals: Dict[str, float] = {}
    def record(self, provider: str, model: str, prompt_tokens: int,
               completion_tokens: int, cost: float) -> CostEntry:
        entry = CostEntry(provider=provider, model=model, prompt_tokens=prompt_tokens,
                          completion_tokens=completion_tokens, cost_usd=cost)
        self._entries.append(entry)
        day = time.strftime("%Y-%m-%d")
        self._daily_totals[day] = self._daily_totals.get(day, 0.0) + cost
        return entry
    def today_total(self) -> float:
        day = time.strftime("%Y-%m-%d")
        return self._daily_totals.get(day, 0.0)
    def is_over_daily_budget(self) -> bool:
        return self.today_total() > self.daily_budget
    def total_spent(self) -> float:
        return sum(e.cost_usd for e in self._entries)
    def entries_count(self) -> int:
        return len(self._entries)
    def get_entries(self, provider: Optional[str] = None, limit: int = 50) -> List[CostEntry]:
        entries = self._entries if not provider else [e for e in self._entries if e.provider == provider]
        return entries[-limit:]
    def daily_totals(self) -> Dict[str, float]:
        return dict(self._daily_totals)
    def clear(self) -> None:
        self._entries.clear()
        self._daily_totals.clear()
    def to_dict(self) -> Dict[str, Any]:
        return {"total_spent": round(self.total_spent(), 6), "today": round(self.today_total(), 6),
                "entries": self.entries_count(), "over_budget": self.is_over_daily_budget()}
