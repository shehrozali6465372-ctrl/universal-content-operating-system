"""LLMCostTracker — Track and budget AI spending."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class CostEntry:
    __slots__ = ("provider", "model", "input_tokens", "output_tokens", "cost", "timestamp")
    def __init__(self, provider: str = "", model: str = "") -> None:
        self.provider = provider; self.model = model
        self.input_tokens = 0; self.output_tokens = 0
        self.cost = 0.0; self.timestamp = time.time()

class LLMCostTracker:
    def __init__(self, daily_budget: float = 100.0, monthly_budget: float = 2000.0) -> None:
        self._daily_budget = daily_budget
        self._monthly_budget = monthly_budget
        self._entries: List[CostEntry] = []

    def record(self, provider: str, model: str, input_tokens: int,
               output_tokens: int, cost: float) -> CostEntry:
        entry = CostEntry(provider, model)
        entry.input_tokens = input_tokens
        entry.output_tokens = output_tokens
        entry.cost = cost
        self._entries.append(entry)
        return entry

    def get_daily_cost(self) -> float:
        cutoff = time.time() - 86400
        return round(sum(e.cost for e in self._entries if e.timestamp > cutoff), 4)

    def get_monthly_cost(self) -> float:
        cutoff = time.time() - 2592000
        return round(sum(e.cost for e in self._entries if e.timestamp > cutoff), 4)

    def is_over_daily_budget(self) -> bool:
        return self.get_daily_cost() > self._daily_budget

    def is_over_monthly_budget(self) -> bool:
        return self.get_monthly_cost() > self._monthly_budget

    def get_remaining_daily(self) -> float:
        return round(max(0, self._daily_budget - self.get_daily_cost()), 4)

    def get_by_provider(self) -> Dict[str, float]:
        costs: Dict[str, float] = {}
        for e in self._entries:
            costs[e.provider] = costs.get(e.provider, 0) + e.cost
        return {k: round(v, 4) for k, v in costs.items()}

    def get_by_model(self) -> Dict[str, float]:
        costs: Dict[str, float] = {}
        for e in self._entries:
            costs[e.model] = costs.get(e.model, 0) + e.cost
        return {k: round(v, 4) for k, v in costs.items()}

    def get_stats(self) -> Dict[str, Any]:
        return {"total_entries": len(self._entries), "daily_cost": self.get_daily_cost(),
                "monthly_cost": self.get_monthly_cost(),
                "daily_budget_remaining": self.get_remaining_daily()}
