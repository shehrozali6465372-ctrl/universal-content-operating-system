"""CostRanker — rank models by cost efficiency."""
from __future__ import annotations
from typing import Any, Dict, List
from .price_calculator import PriceCalculator

class CostRanker:
    def rank(self, prompt_tokens: int, completion_tokens: int,
             models: List[str] | None = None) -> List[Dict[str, Any]]:
        costs = PriceCalculator.compare_models(prompt_tokens, completion_tokens, models)
        ranked = [{"model": m, "cost": c} for m, c in costs.items()]
        ranked.sort(key=lambda x: x["cost"])
        for i, r in enumerate(ranked): r["rank"] = i + 1
        return ranked
    def cheapest(self, prompt_tokens: int, completion_tokens: int) -> Dict[str, Any]:
        ranked = self.rank(prompt_tokens, completion_tokens)
        return ranked[0] if ranked else {"model": "", "cost": 0.0}
