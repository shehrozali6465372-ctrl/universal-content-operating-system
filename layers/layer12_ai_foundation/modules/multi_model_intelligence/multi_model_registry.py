"""MultiModelRegistry — registry of available models and their capabilities."""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class MultiModelRegistry:
    """Registry of available models and their capabilities."""

    def __init__(self) -> None:
        self._models: Dict[str, Dict[str, Any]] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        defaults = {
            "gpt-4o": {"provider": "openai", "capabilities": ["generation", "reasoning", "coding"],
                       "cost_per_token": 0.000005, "max_tokens": 128000},
            "gpt-4o-mini": {"provider": "openai", "capabilities": ["generation"],
                            "cost_per_token": 0.00000015, "max_tokens": 128000},
            "claude-sonnet-4-20250514": {"provider": "anthropic", "capabilities": ["generation", "reasoning", "coding", "creative"],
                                         "cost_per_token": 0.000003, "max_tokens": 200000},
            "gemini-2.0-flash": {"provider": "google", "capabilities": ["generation", "reasoning"],
                                 "cost_per_token": 0.0000001, "max_tokens": 1000000},
            "deepseek-chat": {"provider": "deepseek", "capabilities": ["generation", "coding"],
                              "cost_per_token": 0.0000002, "max_tokens": 128000},
        }
        self._models.update(defaults)

    def register(self, name: str, capabilities: List[str],
                 cost_per_token: float = 0.000001, max_tokens: int = 100000,
                 provider: str = "unknown") -> None:
        self._models[name] = {"provider": provider, "capabilities": capabilities,
                              "cost_per_token": cost_per_token, "max_tokens": max_tokens}

    def unregister(self, name: str) -> bool:
        return self._models.pop(name, None) is not None

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        return self._models.get(name)

    def list_models(self) -> List[str]:
        return list(self._models.keys())

    def get_by_capability(self, capability: str) -> List[str]:
        return [name for name, info in self._models.items()
                if capability in info.get("capabilities", [])]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._models)
