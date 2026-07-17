"""Strategy Selector — Choose best content strategy."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

STRATEGIES = ("educational", "news", "entertainment", "marketing", "branding",
              "sales", "awareness", "community", "viral", "seasonal")


class StrategyProfile:
    """A content strategy profile."""

    __slots__ = ("name", "description", "platforms", "best_for", "weight")

    def __init__(self, name: str = "") -> None:
        self.name = name
        self.description: str = ""
        self.platforms: List[str] = []
        self.best_for: List[str] = []
        self.weight: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "platforms": self.platforms, "weight": self.weight}


class StrategySelector:
    """Select optimal content strategy based on context."""

    def __init__(self) -> None:
        self._strategies: Dict[str, StrategyProfile] = {}
        self._history: List[Dict[str, Any]] = []
        for s in STRATEGIES:
            self._strategies[s] = StrategyProfile(s)

    def select(self, context: Dict[str, Any]) -> StrategyProfile:
        platform = context.get("platform", "").lower()
        goal = context.get("goal", "").lower()
        content_type = context.get("content_type", "").lower()

        candidates = list(self._strategies.values())
        if platform:
            platform_match = [s for s in candidates if platform in s.platforms]
            if platform_match:
                candidates = platform_match

        if goal:
            goal_match = [s for s in candidates if goal in s.best_for]
            if goal_match:
                candidates = goal_match

        selected = max(candidates, key=lambda s: s.weight) if candidates else StrategyProfile("default")
        self._history.append({"strategy": selected.name, "context": context})
        return selected

    def set_platform_strategy(self, platform: str, strategy: str) -> bool:
        if strategy in self._strategies:
            self._strategies[strategy].platforms.append(platform.lower())
            return True
        return False

    def get_strategy(self, name: str) -> Optional[StrategyProfile]:
        return self._strategies.get(name)

    def get_all_strategies(self) -> List[str]:
        return list(self._strategies.keys())

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._history[-limit:]
