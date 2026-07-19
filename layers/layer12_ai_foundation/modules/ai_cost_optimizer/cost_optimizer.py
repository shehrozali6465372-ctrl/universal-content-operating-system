"""CostOptimizer — optimize model selection for cost efficiency."""
from __future__ import annotations
from typing import Any, Dict, List
from .price_calculator import PriceCalculator

class CostOptimizer:
    def __init__(self) -> None:
        self._optimization_log: List[Dict[str, Any]] = []
    def find_cheapest(self, prompt_tokens: int, completion_tokens: int,
                      models: List[str] | None = None) -> str:
        costs = PriceCalculator.compare_models(prompt_tokens, completion_tokens, models)
        return min(costs, key=costs.get)
    def optimize_batch(self, requests: List[Dict[str, Any]],
                       budget: float = 1.0) -> List[Dict[str, Any]]:
        results = []
        remaining = budget
        for req in requests:
            pt = req.get("prompt_tokens", 100)
            ct = req.get("completion_tokens", 100)
            best = self.find_cheapest(pt, ct)
            cost = PriceCalculator.calculate(best, pt, ct)
            if cost <= remaining:
                results.append({"model": best, "estimated_cost": cost, "within_budget": True})
                remaining -= cost
            else:
                cheapest_cost = PriceCalculator.calculate("gpt-4o-mini", pt, ct)
                results.append({"model": "gpt-4o-mini", "estimated_cost": cheapest_cost,
                                "within_budget": cheapest_cost <= remaining})
                remaining -= cheapest_cost
        return results
    def suggest_model(self, quality_needed: str = "medium",
                      max_budget: float = 0.01) -> str:
        if quality_needed == "high":
            return "gpt-4o" if max_budget >= 0.01 else "claude-sonnet-4-20250514"
        elif quality_needed == "medium":
            return "gpt-4o-mini" if max_budget >= 0.001 else "gemini-2.0-flash"
        return "gemini-2.0-flash"
