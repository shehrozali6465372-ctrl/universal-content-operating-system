"""BudgetPlanner — validated budget allocation and spend accounting."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_BP_COUNTER = itertools.count(1)
BUDGET_CATEGORIES = ("ai_api", "gpu", "marketing", "content", "research",
                     "infrastructure", "tools", "personnel", "other")


class BudgetAllocation:
    def __init__(self, category: str = "other", allocated: float = 0.0) -> None:
        self.allocation_id = f"balloc_{next(_BP_COUNTER)}"
        self.category = category if category in BUDGET_CATEGORIES else "other"
        self.allocated = max(0.0, float(allocated))
        self.spent = 0.0
        self.reserved = 0.0
        self.notes = ""
        self.created_at = time.time()

    def get_remaining(self) -> float:
        return round(max(0.0, self.allocated - self.spent - self.reserved), 2)

    def get_utilization(self) -> float:
        return round(self.spent / self.allocated, 4) if self.allocated else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"allocation_id": self.allocation_id, "category": self.category,
                "allocated": self.allocated, "spent": self.spent,
                "remaining": self.get_remaining(), "utilization": self.get_utilization()}


class BudgetPlanner:
    def __init__(self, total_budget: float = 0.0, max_history: int = 10000) -> None:
        if total_budget < 0 or max_history <= 0:
            raise ValueError("invalid budget or history limit")
        self._total_budget = float(total_budget)
        self._allocations: List[BudgetAllocation] = []
        self._alloc_index: Dict[str, BudgetAllocation] = {}
        self._daily_spend: List[Dict[str, float]] = []
        self._max_history = max_history

    def allocate(self, category: str, amount: float) -> BudgetAllocation:
        if amount < 0:
            raise ValueError("amount must be non-negative")
        existing = self._alloc_index.get(category)
        if existing:
            if self._total_budget and self.get_total_allocated() + amount > self._total_budget:
                raise ValueError("allocation exceeds total budget")
            existing.allocated += amount
            return existing
        if self._total_budget and self.get_total_allocated() + amount > self._total_budget:
            raise ValueError("allocation exceeds total budget")
        allocation = BudgetAllocation(category, amount)
        self._allocations.append(allocation)
        self._alloc_index[category] = allocation
        return allocation

    def record_spend(self, category: str, amount: float) -> bool:
        allocation = self._alloc_index.get(category)
        if allocation is None or amount < 0 or allocation.get_remaining() < amount:
            return False
        allocation.spent += amount
        self._daily_spend.append({"category": category, "amount": amount, "timestamp": time.time()})
        if len(self._daily_spend) > self._max_history:
            del self._daily_spend[:-self._max_history]
        return True

    def reserve(self, category: str, amount: float) -> bool:
        allocation = self._alloc_index.get(category)
        if allocation is None or amount < 0 or allocation.get_remaining() < amount:
            return False
        allocation.reserved += amount
        return True

    def get_allocation(self, category: str) -> Optional[BudgetAllocation]:
        return self._alloc_index.get(category)

    def get_all_allocations(self) -> List[BudgetAllocation]:
        return list(self._allocations)

    def get_total_allocated(self) -> float:
        return round(sum(a.allocated for a in self._allocations), 2)

    def get_total_spent(self) -> float:
        return round(sum(a.spent for a in self._allocations), 2)

    def get_total_remaining(self) -> float:
        return round(sum(a.get_remaining() for a in self._allocations), 2)

    def get_utilization_report(self) -> Dict[str, float]:
        return {a.category: a.get_utilization() for a in self._allocations}

    def forecast_remaining_days(self, daily_rate: float = 0.0) -> float:
        if daily_rate <= 0:
            if not self._daily_spend:
                return float("inf")
            daily_rate = sum(item["amount"] for item in self._daily_spend[-7:]) / min(7, len(self._daily_spend))
        return round(self.get_total_remaining() / daily_rate, 1) if daily_rate > 0 else float("inf")

    def set_total_budget(self, amount: float) -> None:
        if amount < self.get_total_allocated():
            raise ValueError("total budget cannot be below current allocations")
        self._total_budget = float(amount)

    def get_stats(self) -> Dict[str, Any]:
        return {"total_budget": self._total_budget, "total_allocated": self.get_total_allocated(),
                "total_spent": self.get_total_spent(),
                "total_remaining": self.get_total_remaining(), "allocations": len(self._allocations)}
