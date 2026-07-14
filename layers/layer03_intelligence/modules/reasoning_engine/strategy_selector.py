"""Strategy Selector - Selects optimal strategy based on conditions."""
from __future__ import annotations
from typing import Dict, List, Optional


class Strategy:
    """A named strategy with conditions and parameters."""
    __slots__ = ("name", "description", "conditions", "parameters", "priority", "enabled")

    def __init__(self, name: str = "", description: str = "",
                 conditions: Optional[Dict] = None, parameters: Optional[Dict] = None,
                 priority: int = 0):
        self.name = name
        self.description = description
        self.conditions = conditions or {}
        self.parameters = parameters or {}
        self.priority = priority
        self.enabled = True

    def matches(self, context: Dict) -> float:
        if not self.conditions:
            return 0.5
        match_count = 0
        for key, expected in self.conditions.items():
            actual = context.get(key)
            if actual == expected or (isinstance(expected, list) and actual in expected):
                match_count += 1
            elif isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                if abs(actual - expected) / max(abs(expected), 1) < 0.2:
                    match_count += 1
        return match_count / max(len(self.conditions), 1)

    def to_dict(self) -> Dict:
        return {"name": self.name, "description": self.description,
                "conditions": dict(self.conditions), "parameters": dict(self.parameters),
                "priority": self.priority, "enabled": self.enabled}


class StrategyResult:
    """Result of strategy selection."""
    __slots__ = ("selected", "alternatives", "confidence", "reasoning")

    def __init__(self) -> None:
        self.selected: Optional[Strategy] = None
        self.alternatives: List[Strategy] = []
        self.confidence = 0.0
        self.reasoning: List[str] = []

    def to_dict(self) -> Dict:
        return {
            "selected": self.selected.to_dict() if self.selected else None,
            "alternatives": [s.to_dict() for s in self.alternatives[:3]],
            "confidence": round(self.confidence, 3),
            "reasoning": list(self.reasoning),
        }


class StrategySelector:
    """Selects the best strategy based on context matching."""

    def __init__(self) -> None:
        self._strategies: List[Strategy] = []

    def add_strategy(self, strategy: Strategy) -> None:
        self._strategies.append(strategy)
        self._strategies.sort(key=lambda s: s.priority, reverse=True)

    def select(self, context: Dict) -> StrategyResult:
        result = StrategyResult()
        scored = []
        for s in self._strategies:
            if not s.enabled:
                continue
            score = s.matches(context)
            scored.append((s, score))

        scored.sort(key=lambda x: (x[1], x[0].priority), reverse=True)

        if scored:
            result.selected = scored[0][0]
            result.alternatives = [s for s, _ in scored[1:3]]
            result.confidence = scored[0][1]
            result.reasoning.append(
                f"Selected '{result.selected.name}' with match score {scored[0][1]:.2f}"
            )

        return result

    def select_all_matching(self, context: Dict, threshold: float = 0.5) -> List[Strategy]:
        return [s for s in self._strategies if s.enabled and s.matches(context) >= threshold]

    def count(self) -> int:
        return len(self._strategies)
