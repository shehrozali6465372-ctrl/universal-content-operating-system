"""RecommendationEngine — content and strategy recommendations."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional


class Recommendation:
    __slots__ = ("rec_id", "category", "title", "description", "confidence",
                 "priority", "metadata")

    def __init__(self, category: str, title: str, description: str = "",
                 confidence: float = 0.8, priority: int = 5) -> None:
        self.rec_id = f"rec_{int(time.time() * 1000) % 100000}"
        self.category = category
        self.title = title
        self.description = description
        self.confidence = confidence
        self.priority = priority
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"rec_id": self.rec_id, "category": self.category,
                "title": self.title, "confidence": self.confidence,
                "priority": self.priority}


class RecommendationEngine:
    def __init__(self) -> None:
        self._rules: List[Callable] = []
        self._history: List[Dict[str, Any]] = []

    def add_rule(self, rule_fn: Callable) -> None:
        self._rules.append(rule_fn)

    def generate(self, context: Dict[str, Any]) -> List[Recommendation]:
        recommendations = []
        for rule in self._rules:
            try:
                result = rule(context)
                if isinstance(result, list):
                    recommendations.extend(result)
                elif isinstance(result, Recommendation):
                    recommendations.append(result)
            except Exception:
                pass
        recommendations.sort(key=lambda r: (-r.priority, -r.confidence))
        self._history.extend([r.to_dict() for r in recommendations])
        return recommendations

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)

    def count_rules(self) -> int:
        return len(self._rules)
