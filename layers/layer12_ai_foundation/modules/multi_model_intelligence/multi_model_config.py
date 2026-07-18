"""Configuration for Multi Model Intelligence."""
from __future__ import annotations

from typing import Any, Dict, List


class MultiModelConfig:
    """Configuration for the multi-model intelligence system."""

    def __init__(self, **kwargs: Any) -> None:
        self.models: List[str] = kwargs.get("models", ["gpt-4o", "claude-sonnet-4-20250514", "gemini-2.0-flash"])
        self.consensus_method: str = kwargs.get("consensus_method", "majority")
        self.min_models: int = kwargs.get("min_models", 2)
        self.max_models: int = kwargs.get("max_models", 10)
        self.confidence_threshold: float = kwargs.get("confidence_threshold", 0.6)
        self.timeout_seconds: float = kwargs.get("timeout_seconds", 30.0)
        self.enable_voting: bool = kwargs.get("enable_voting", True)
        self.enable_ranking: bool = kwargs.get("enable_ranking", True)
        self.enable_consensus: bool = kwargs.get("enable_consensus", True)
        self.enable_caching: bool = kwargs.get("enable_caching", True)
        self.cache_ttl: int = kwargs.get("cache_ttl", 3600)
        self.voting_weights: Dict[str, float] = kwargs.get("voting_weights", {})
        self.rank_weights: Dict[str, float] = kwargs.get("rank_weights", {
            "quality": 0.3, "relevance": 0.25, "creativity": 0.2,
            "accuracy": 0.15, "conciseness": 0.1,
        })
        self.parallel_max: int = kwargs.get("parallel_max", 5)
        self.retry_count: int = kwargs.get("retry_count", 2)
        self.fallback_model: str = kwargs.get("fallback_model", "gpt-4o-mini")

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
