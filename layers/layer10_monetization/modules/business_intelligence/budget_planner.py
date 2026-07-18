"""BudgetPlanner — Manage AI costs, API costs, and business budgets."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_BP_COUNTER = itertools.count(1)

BUDGET_CATEGORIES = (
    "ai_api", "gpu", "marketing", "content", "research",
    "infrastructure", "tools", "personnel", "other",
)


class BudgetAllocation:
    """A budget allocation entry."""

    __slots__ = ("allocation_id", "category", "allocated", "spent",
                 "reserved", "notes", "created_at")

    def __init__(self, category: str = "other", allocated: float = 0.0) -> None:
        self.allocation_id: str = f"balloc_{next(_BP_COUNTER)}"
        self.category = category if category in BUDGET_CATEGORIES else "other"
        self.allocated = max(0.0, allocated)
        self.spent: float = 0.0
        self.reserved: float = 0.0
        self.notes: str = ""
        self.created_at: float = time.time()

    def get_remaining(self) -> float:
        return round(max(0.0, self.allocated - self.spent - self.reserved), 2)

    def get_utilization(self) -> float:
        if self.allocated == 0:
            return 0.0
        return round(self.spent / self.allocated, 4)

    def to_dict(self) -> Dict[str, Any]:
        return {"allocation_id": self.allocation_id, "category": self.category,
                "allocated": self.allocated, "spent": self.spent,
                "remaining": self.get_remaining(),
                "utilization": self.get_utilization()}


class BudgetPlanner:
    """Manage budgets across categories with forecasting."""

    def __init__(self, total_budget: float = 0.0) -> None:
        self._total_budget = total_budget
        self._allocations: List[BudgetAllocation] = []
        self._alloc_index: Dict[str, BudgetAllocation] = {}
        self._daily_spend: List[Dict[str, float]] = []

    def allocate(self, category: str, amount: float) -> BudgetAllocation:
        existing = self._alloc_index.get(category)
        if existing:
            existing.allocated += amount
            return existing
        alloc = BudgetAllocation(category, amount)
        self._allocations.append(alloc)
        self._alloc_index[category] = alloc
        return alloc

    def record_spend(self, category: str, amount: float) -> bool:
        alloc = self._alloc_index.get(category)
        if alloc is None or amount < 0:
            return False
        alloc.spent += amount
        self._daily_spend.append({"category": category, "amount": amount,
                                   "timestamp": time.time()})
        return True

    def reserve(self, category: str, amount: float) -> bool:
        alloc = self._alloc_index.get(category)
        if alloc is None:
            return False
        if alloc.get_remaining() >= amount:
            alloc.reserved += amount
            return True
        return False

    def get_allocation(self, category: str) -> Optional[BudgetAllocation]:
        return self._alloc_index.get(category)

    def get_all_allocations(self) -> List[BudgetAllocation]:
        return list(self._allocations)

    def get_total_spent(self) -> float:
        return round(sum(a.spent for a in self._allocations), 2)

    def get_total_remaining(self) -> float:
        return round(sum(a.get_remaining() for a in self._allocations), 2)

    def get_utilization_report(self) -> Dict[str, float]:
        return {a.category: a.get_utilization() for a in self._allocations}

    def forecast_remaining_days(self, daily_rate: float = 0.0) -> float:
        if daily_rate <= 0:
            if len(self._daily_spend) >= 2:
                amounts = [d["amount"] for d in self._daily_spend[-7:]]
                daily_rate = sum(amounts) / len(amounts)
            else:
                return float("inf")
        remaining = self.get_total_remaining()
        if daily_rate <= 0:
            return float("inf")
        return round(remaining / daily_rate, 1)

    def set_total_budget(self, amount: float) -> None:
        self._total_budget = max(0.0, amount)

    def get_stats(self) -> Dict[str, Any]:
        return {"total_budget": self._total_budget,
                "total_spent": self.get_total_spent(),
                "total_remaining": self.get_total_remaining(),
                "allocations": len(self._allocations)}
