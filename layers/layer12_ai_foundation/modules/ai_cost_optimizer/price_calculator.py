"""PriceCalculator — calculate costs for various models and providers."""
from __future__ import annotations
from typing import Dict

class PricePerToken:
    PROMPT_PRICE: Dict[str, float] = {
        "gpt-4o": 0.005, "gpt-4o-mini": 0.00015, "gpt-4-turbo": 0.01,
        "claude-sonnet-4-20250514": 0.003, "claude-3-haiku": 0.00025,
        "gemini-2.0-flash": 0.0001, "gemini-pro": 0.00025,
        "deepseek-chat": 0.0002, "mistral-large": 0.004,
    }
    COMPLETION_PRICE: Dict[str, float] = {
        "gpt-4o": 0.015, "gpt-4o-mini": 0.0006, "gpt-4-turbo": 0.03,
        "claude-sonnet-4-20250514": 0.015, "claude-3-haiku": 0.00125,
        "gemini-2.0-flash": 0.0004, "gemini-pro": 0.0005,
        "deepseek-chat": 0.001, "mistral-large": 0.012,
    }

class PriceCalculator:
    @staticmethod
    def calculate(model: str, prompt_tokens: int, completion_tokens: int) -> float:
        prompt_rate = PricePerToken.PROMPT_PRICE.get(model, 0.01)
        completion_rate = PricePerToken.COMPLETION_PRICE.get(model, 0.03)
        return prompt_tokens * prompt_rate / 1000 + completion_tokens * completion_rate / 1000
    @staticmethod
    def compare_models(prompt_tokens: int, completion_tokens: int,
                       models: list | None = None) -> Dict[str, float]:
        models = models or list(PricePerToken.PROMPT_PRICE.keys())
        return {m: round(PriceCalculator.calculate(m, prompt_tokens, completion_tokens), 6) for m in models}
