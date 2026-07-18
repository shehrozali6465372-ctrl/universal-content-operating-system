"""MemoryConfig — configuration for the AI memory system."""
from __future__ import annotations

from typing import Any, Dict


class MemoryConfig:
    """Configuration for the AI memory layer."""

    def __init__(self, **kwargs: Any) -> None:
        self.short_term_capacity: int = kwargs.get("short_term_capacity", 50)
        self.long_term_capacity: int = kwargs.get("long_term_capacity", 5000)
        self.semantic_capacity: int = kwargs.get("semantic_capacity", 2000)
        self.episodic_capacity: int = kwargs.get("episodic_capacity", 1000)
        self.conversation_capacity: int = kwargs.get("conversation_capacity", 100)
        self.cache_size: int = kwargs.get("cache_size", 200)
        self.cache_ttl: int = kwargs.get("cache_ttl", 300)
        self.enable_sync: bool = kwargs.get("enable_sync", True)
        self.enable_consolidation: bool = kwargs.get("enable_consolidation", True)
        self.enable_forgetting: bool = kwargs.get("enable_forgetting", True)
        self.decay_rate: float = kwargs.get("decay_rate", 0.01)
        self.default_half_life_days: float = kwargs.get("default_half_life_days", 30.0)
        self.vector_dimensions: int = kwargs.get("vector_dimensions", 128)

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
