"""PriceCalculator — calculate costs using an explicit model price registry."""
from __future__ import annotations

from typing import Dict


class PricePerToken:
    """Prices are USD per 1,000 tokens."""

    PROMPT_PRICE: Dict[str, float] = {
        "gpt-5.6-luna": 0.0002,
        "gpt-5.6-terra": 0.002,
        "gpt-5.6-sol": 0.004,
        "gemini-3.8-flash": 0.00075,
        "deepseek-flash": 0.0003,
        "deepseek-v4-pro": 0.00132,
        "gpt-4o-mini": 0.00015,
    }
    COMPLETION_PRICE: Dict[str, float] = {
        "gpt-5.6-luna": 0.0012,
        "gpt-5.6-terra": 0.012,
        "gpt-5.6-sol": 0.020,
        "gemini-3.8-flash": 0.00375,
        "deepseek-flash": 0.0012,
        "deepseek-v4-pro": 0.00396,
        "gpt-4o-mini": 0.0006,
    }


class PriceCalculator:
    @staticmethod
    def calculate(
        model: str, prompt_tokens: int, completion_tokens: int
    ) -> float:
        if model not in PricePerToken.PROMPT_PRICE:
            raise ValueError(f"No price configured for model: {model}")
        if prompt_tokens < 0 or completion_tokens < 0:
            raise ValueError("token counts must be non-negative")
        return (
            prompt_tokens * PricePerToken.PROMPT_PRICE[model] / 1000
            + completion_tokens * PricePerToken.COMPLETION_PRICE[model] / 1000
        )

    @staticmethod
    def compare_models(
        prompt_tokens: int,
        completion_tokens: int,
        models: list | None = None,
    ) -> Dict[str, float]:
        selected = models or list(PricePerToken.PROMPT_PRICE)
        return {
            model: round(
                PriceCalculator.calculate(model, prompt_tokens, completion_tokens),
                6,
            )
            for model in selected
        }
