"""MultiModelOptimizer — optimize multi-model operations for cost/quality."""
from __future__ import annotations

from typing import Any, Dict, List

from .models import ModelResponse


class MultiModelOptimizer:
    """Optimize multi-model operations for cost, speed, and quality."""

    def __init__(self) -> None:
        self._optimization_log: List[Dict[str, Any]] = []

    def optimize_model_selection(
        self,
        available_models: List[str],
        task_type: str = "generation",
        budget: float = 1.0,
        quality_threshold: float = 0.7,
    ) -> List[str]:
        cost_map = {
            "gpt-5.6-luna": 0.0002,
            "gpt-5.6-sol": 0.004,
            "gemini-3.8-flash": 0.00075,
            "deepseek-flash": 0.0003,
            "deepseek-v4-pro": 0.00132,
        }
        task_models = {
            "generation": [
                "gpt-5.6-luna",
                "gemini-3.8-flash",
                "deepseek-flash",
                "gpt-5.6-sol",
            ],
            "reasoning": ["gpt-5.6-sol", "deepseek-v4-pro"],
            "coding": ["gpt-5.6-sol", "deepseek-v4-pro", "gpt-5.6-luna"],
            "creative": ["gpt-5.6-sol", "gpt-5.6-luna"],
            "review": ["gpt-5.6-luna", "gemini-3.8-flash", "deepseek-flash"],
        }

        candidates = task_models.get(task_type, available_models)
        filtered = [model for model in candidates if model in available_models]
        filtered.sort(key=lambda model: cost_map.get(model, 0.01))
        return filtered

    def optimize_consensus(
        self, responses: List[ModelResponse]
    ) -> Dict[str, Any]:
        if not responses:
            return {"action": "none", "reason": "no responses"}

        successful = [response for response in responses if response.is_success]
        if not successful:
            return {"action": "retry", "reason": "all failed"}

        best = max(successful, key=lambda response: response.confidence)
        avg_confidence = sum(
            response.confidence for response in successful
        ) / len(successful)

        if avg_confidence > 0.8:
            return {
                "action": "accept",
                "best_model": best.model,
                "confidence": avg_confidence,
            }
        if avg_confidence > 0.5:
            return {
                "action": "accept_with_review",
                "best_model": best.model,
                "confidence": avg_confidence,
            }
        return {
            "action": "retry_with_different_models",
            "confidence": avg_confidence,
        }

    def reduce_cost(self, models: List[str], max_models: int = 3) -> List[str]:
        return models[:max_models]

    def get_log(self) -> List[Dict[str, Any]]:
        return list(self._optimization_log)
