"""provider_cost.py — Provider cost tracking."""
from __future__ import annotations
from typing import Any, Dict

# Default pricing per 1M tokens
DEFAULT_PRICING: Dict[str, Dict[str, float]] = {
    "openai": {"gpt-4o": 2.5, "gpt-4o-mini": 0.15, "gpt-4-turbo": 10.0, "o1": 15.0},
    "claude": {"claude-sonnet-4-20250514": 3.0, "claude-3-5-sonnet-20241022": 3.0,
               "claude-3-5-haiku-20241022": 0.8, "claude-3-opus-20240229": 15.0},
    "gemini": {"gemini-2.0-flash": 0.1, "gemini-2.0-pro": 1.25, "gemini-1.5-pro": 1.25},
    "deepseek": {"deepseek-chat": 0.14, "deepseek-reasoner": 0.55},
    "mistral": {"mistral-large-latest": 2.0, "mistral-small-latest": 0.1},
    "cohere": {"command-r-plus": 2.5, "command-r": 0.15},
    "grok": {"grok-2": 2.0, "grok-3": 3.0},
    "ollama": {"*": 0.0},
    "llama": {"*": 0.2},
    "qwen": {"qwen-max": 1.6, "qwen-plus": 0.4},
    "openrouter": {"*": 0.5},
}


class ProviderCost:
    """Tracks costs across all providers."""

    def __init__(self) -> None:
        self._costs: Dict[str, Dict[str, float]] = {}
        self._total_tokens: Dict[str, int] = {}
        self._budget_limit: float = float("inf")

    def set_budget(self, limit: float) -> None:
        self._budget_limit = limit

    def record(self, provider: str, model: str, prompt_tokens: int,
               completion_tokens: int) -> float:
        cost = self._calculate_cost(provider, model, prompt_tokens, completion_tokens)
        if provider not in self._costs:
            self._costs[provider] = {"total_cost": 0.0, "input_cost": 0.0, "output_cost": 0.0}
            self._total_tokens[provider] = 0
        self._costs[provider]["total_cost"] += cost
        self._costs[provider]["input_cost"] += cost * 0.4
        self._costs[provider]["output_cost"] += cost * 0.6
        self._total_tokens[provider] = self._total_tokens.get(provider, 0) + prompt_tokens + completion_tokens
        return cost

    def _calculate_cost(self, provider: str, model: str,
                        prompt_tokens: int, completion_tokens: int) -> float:
        pricing = DEFAULT_PRICING.get(provider, {})
        price_per_m = pricing.get(model, pricing.get("*", 0.1))
        return (prompt_tokens + completion_tokens) * price_per_m / 1_000_000

    def get_cost(self, provider: str) -> float:
        return self._costs.get(provider, {}).get("total_cost", 0.0)

    def get_total_cost(self) -> float:
        return sum(c.get("total_cost", 0.0) for c in self._costs.values())

    def get_remaining_budget(self) -> float:
        return max(0.0, self._budget_limit - self.get_total_cost())

    def is_over_budget(self) -> bool:
        return self.get_total_cost() > self._budget_limit

    def get_breakdown(self) -> Dict[str, Dict[str, float]]:
        return {k: dict(v) for k, v in self._costs.items()}

    def to_dict(self) -> Dict[str, Any]:
        return {"breakdown": self.get_breakdown(), "total": self.get_total_cost(),
                "budget": self._budget_limit, "remaining": self.get_remaining_budget()}
