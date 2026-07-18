"""MultiModelStrategy — strategy patterns for multi-model operations."""
from __future__ import annotations

from typing import Any, Dict, List


class MultiModelStrategy:
    """Define strategies for multi-model selection."""

    STRATEGIES = {
        "fastest": {"prefer_low_latency": True, "prefer_high_confidence": False},
        "cheapest": {"prefer_low_cost": True, "prefer_high_confidence": False},
        "best_quality": {"prefer_low_latency": False, "prefer_high_confidence": True},
        "balanced": {"prefer_low_latency": True, "prefer_high_confidence": True},
        "consensus": {"require_agreement": True, "min_agreement": 0.6},
    }

    def __init__(self, name: str = "balanced") -> None:
        self.name = name
        self.config = self.STRATEGIES.get(name, self.STRATEGIES["balanced"])
        self._custom: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._custom[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._custom.get(key, self.config.get(key, default))

    def to_dict(self) -> Dict[str, Any]:
        result = dict(self.config)
        result.update(self._custom)
        result["name"] = self.name
        return result

    @classmethod
    def available_strategies(cls) -> List[str]:
        return list(cls.STRATEGIES.keys())
