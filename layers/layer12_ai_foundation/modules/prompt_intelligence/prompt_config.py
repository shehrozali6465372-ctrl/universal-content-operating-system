"""PromptConfig — configuration for the prompt intelligence system."""
from __future__ import annotations

from typing import Any, Dict, List


class PromptConfig:
    """Configuration for prompt intelligence system."""

    def __init__(self, **kwargs: Any) -> None:
        self.default_role: str = kwargs.get("default_role", "assistant")
        self.max_prompt_length: int = kwargs.get("max_prompt_length", 10000)
        self.max_fewshot_examples: int = kwargs.get("max_fewshot_examples", 5)
        self.enable_optimization: bool = kwargs.get("enable_optimization", True)
        self.enable_caching: bool = kwargs.get("enable_caching", True)
        self.enable_validation: bool = kwargs.get("enable_validation", True)
        self.enable_events: bool = kwargs.get("enable_events", True)
        self.optimization_techniques: List[str] = kwargs.get("optimization_techniques", [
            "clarity", "specificity", "context_enrichment",
            "constraint_addition", "role_assignment", "output_format",
        ])
        self.default_cot_strategy: str = kwargs.get("default_cot_strategy", "basic")
        self.cache_ttl: int = kwargs.get("cache_ttl", 3600)
        self.max_memory_entries: int = kwargs.get("max_memory_entries", 1000)

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
