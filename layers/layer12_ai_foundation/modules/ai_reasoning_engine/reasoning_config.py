"""ReasoningConfig — configuration for the reasoning engine."""
from __future__ import annotations

from typing import Any, Dict


class ReasoningConfig:
    """Configuration for the AI reasoning engine."""

    def __init__(self, **kwargs: Any) -> None:
        self.default_type: str = kwargs.get("default_type", "logical")
        self.max_chain_steps: int = kwargs.get("max_chain_steps", 20)
        self.min_confidence: float = kwargs.get("min_confidence", 0.3)
        self.enable_verification: bool = kwargs.get("enable_verification", True)
        self.enable_reflection: bool = kwargs.get("enable_reflection", True)
        self.timeout_seconds: float = kwargs.get("timeout_seconds", 30.0)
        self.max_retries: int = kwargs.get("max_retries", 2)
        self.enable_counterfactual: bool = kwargs.get("enable_counterfactual", True)
        self.enable_analogy: bool = kwargs.get("enable_analogy", True)

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
