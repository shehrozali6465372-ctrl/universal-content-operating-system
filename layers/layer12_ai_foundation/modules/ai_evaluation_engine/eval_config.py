"""EvalConfig — configuration for evaluation engine."""
from __future__ import annotations
from typing import Any, Dict

class EvalConfig:
    def __init__(self, **kwargs: Any) -> None:
        self.min_quality_score: float = kwargs.get("min_quality_score", 0.5)
        self.min_accuracy: float = kwargs.get("min_accuracy", 0.6)
        self.max_hallucination_rate: float = kwargs.get("max_hallucination_rate", 0.1)
        self.max_bias_score: float = kwargs.get("max_bias_score", 0.3)
        self.enable_all_checks: bool = kwargs.get("enable_all_checks", True)
        self.fail_on_safety: bool = kwargs.get("fail_on_safety", True)
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
