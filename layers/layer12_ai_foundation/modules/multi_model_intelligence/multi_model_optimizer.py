"""MultiModelOptimizer — optimize multi-model operations for cost/quality."""
from __future__ import annotations

from typing import Any, Dict, List

from .models import ModelResponse


class MultiModelOptimizer:
    """Optimize multi-model operations for cost, speed, and quality."""

    def __init__(self) -> None:
        self._optimization_log: List[Dict[str, Any]] = []

    def optimize_model_selection(self, available_models: List[str],
                                 task_type: str = "generation",
                                 budget: float = 1.0,
                                 quality_threshold: float = 0.7) -> List[str]:
        # Simple optimization: prefer cheaper models, filter by task capability
        cost_map = {
            "gpt-4o": 0.005, "gpt-4o-mini": 0.00015,
            "claude-sonnet-4-20250514": 0.003, "gemini-2.0-flash": 0.0001,
            "deepseek-chat": 0.0002,
        }
        task_models = {
            "generation": ["gpt-4o", "claude-sonnet-4-20250514", "gemini-2.0-flash", "gpt-4o-mini"],
            "reasoning": ["gpt-4o", "claude-sonnet-4-20250514"],
            "coding": ["gpt-4o", "claude-sonnet-4-20250514", "deepseek-chat"],
            "creative": ["gpt-4o", "claude-sonnet-4-20250514"],
            "review": ["gpt-4o", "claude-sonnet-4-20250514", "gemini-2.0-flash"],
        }

        candidates = task_models.get(task_type, available_models)
        filtered = [m for m in candidates if m in available_models]
        filtered.sort(key=lambda m: cost_map.get(m, 0.01))
        return filtered

    def optimize_consensus(self, responses: List[ModelResponse]) -> Dict[str, Any]:
        if not responses:
            return {"action": "none", "reason": "no responses"}

        successful = [r for r in responses if r.is_success]
        if not successful:
            return {"action": "retry", "reason": "all failed"}

        best = max(successful, key=lambda r: r.confidence)
        avg_confidence = sum(r.confidence for r in successful) / len(successful)

        if avg_confidence > 0.8:
            return {"action": "accept", "best_model": best.model,
                    "confidence": avg_confidence}
        elif avg_confidence > 0.5:
            return {"action": "accept_with_review", "best_model": best.model,
                    "confidence": avg_confidence}
        else:
            return {"action": "retry_with_different_models", "confidence": avg_confidence}

    def reduce_cost(self, models: List[str], max_models: int = 3) -> List[str]:
        return models[:max_models]

    def get_log(self) -> List[Dict[str, Any]]:
        return list(self._optimization_log)
