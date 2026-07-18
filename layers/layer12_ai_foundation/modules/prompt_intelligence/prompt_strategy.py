"""PromptStrategy — strategy patterns for different prompt use cases."""
from __future__ import annotations

from typing import Any, Dict, List


class PromptStrategy:
    """Define and manage prompt strategies for different scenarios."""

    STRATEGIES: Dict[str, Dict[str, Any]] = {
        "concise": {"max_tokens": 200, "style": "brief", "priority": "speed"},
        "detailed": {"max_tokens": 2000, "style": "thorough", "priority": "quality"},
        "creative": {"temperature": 0.9, "style": "creative", "priority": "originality"},
        "factual": {"temperature": 0.1, "style": "precise", "priority": "accuracy"},
        "balanced": {"temperature": 0.5, "style": "balanced", "priority": "general"},
    }

    def __init__(self, name: str = "balanced") -> None:
        self.name = name
        self.config = dict(self.STRATEGIES.get(name, self.STRATEGIES["balanced"]))
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
    def available(cls) -> List[str]:
        return list(cls.STRATEGIES.keys())
