"""cost_optimizer.py — Storage cost optimization."""
from __future__ import annotations
from typing import Any, Dict, List


class CostOptimizer:
    """Optimizes storage costs."""

    def __init__(self, budget: float = 1000.0) -> None:
        self._budget = budget
        self._costs: Dict[str, float] = {}
        self._optimizations: List[Dict[str, Any]] = []

    def record_cost(self, store_name: str, cost: float) -> None:
        self._costs[store_name] = self._costs.get(store_name, 0) + cost

    def get_total_cost(self) -> float:
        return sum(self._costs.values())

    def get_remaining_budget(self) -> float:
        return max(0.0, self._budget - self.get_total_cost())

    def suggest_optimization(self, store_name: str, current_cost: float,
                              target_cost: float) -> Dict[str, Any]:
        saving = current_cost - target_cost
        result = {"store": store_name, "saving": saving, "target": target_cost}
        self._optimizations.append(result)
        return result

    def get_optimizations(self) -> List[Dict[str, Any]]:
        return list(self._optimizations)

    def stats(self) -> Dict[str, Any]:
        return {"total_cost": self.get_total_cost(), "budget": self._budget,
                "stores": len(self._costs)}
