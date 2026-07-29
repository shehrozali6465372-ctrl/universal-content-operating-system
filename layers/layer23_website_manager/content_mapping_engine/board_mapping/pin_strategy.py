"""PinStrategyEngine — Automatically select the best pin format and style."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.content_mapping_engine.models.content_mapping import (
    ContentIntent, PinStrategy,
)
from layers.layer23_website_manager.content_mapping_engine.exceptions import PinStrategyError


# Strategy rules based on content type and intent
STRATEGY_RULES: Dict[str, List[Dict[str, Any]]] = {
    "list": [
        {"strategy": PinStrategy.STANDARD, "score": 0.7, "reason": "Standard pin works for list content"},
        {"strategy": PinStrategy.CAROUSEL, "score": 0.9, "reason": "Carousel ideal for list content"},
        {"strategy": PinStrategy.IDEA, "score": 0.6, "reason": "Idea pin can showcase list items"},
    ],
    "guide": [
        {"strategy": PinStrategy.RICH, "score": 0.9, "reason": "Rich pin perfect for guides"},
        {"strategy": PinStrategy.STANDARD, "score": 0.7, "reason": "Standard pin works for guides"},
    ],
    "recipe": [
        {"strategy": PinStrategy.IDEA, "score": 0.9, "reason": "Idea pin ideal for recipes"},
        {"strategy": PinStrategy.STANDARD, "score": 0.7, "reason": "Standard pin works for recipes"},
    ],
    "review": [
        {"strategy": PinStrategy.PRODUCT, "score": 0.9, "reason": "Product pin perfect for reviews"},
        {"strategy": PinStrategy.STANDARD, "score": 0.6, "reason": "Standard pin ok for reviews"},
    ],
    "article": [
        {"strategy": PinStrategy.RICH, "score": 0.85, "reason": "Rich pin best for articles"},
        {"strategy": PinStrategy.STANDARD, "score": 0.75, "reason": "Standard pin works for articles"},
        {"strategy": PinStrategy.IDEA, "score": 0.6, "reason": "Idea pin for visual articles"},
    ],
}

INTENT_STRATEGY: Dict[str, PinStrategy] = {
    "educational": PinStrategy.RICH,
    "inspirational": PinStrategy.IDEA,
    "commercial": PinStrategy.PRODUCT,
    "informational": PinStrategy.STANDARD,
    "entertainment": PinStrategy.IDEA,
}


class PinStrategyEngine:
    """Select optimal pin strategy based on content type, intent, and niche."""

    def __init__(self) -> None:
        self._strategy_log: List[dict] = []
        self._total_analyses = 0

    def select_strategy(self, content_type: str = "article",
                         intent: ContentIntent = ContentIntent.INFORMATIONAL,
                         niche: str = "", keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """Select the best pin strategy for this content."""
        # Get strategies for content type
        strategies = STRATEGY_RULES.get(content_type, STRATEGY_RULES["article"])

        # Boost score based on intent match
        intent_best = INTENT_STRATEGY.get(intent.value, PinStrategy.STANDARD)
        for s in strategies:
            if s["strategy"] == intent_best:
                s["score"] = min(1.0, s["score"] + 0.1)

        # Pick highest scored strategy
        best = max(strategies, key=lambda s: s["score"])
        alternatives = [s for s in strategies if s["strategy"] != best["strategy"]]

        result = {
            "selected_strategy": best["strategy"].value,
            "reason": best["reason"],
            "confidence": round(best["score"], 2),
            "alternatives": [a["strategy"].value for a in alternatives[:2]],
        }

        self._strategy_log.append(result)
        self._total_analyses += 1
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {"total_analyses": self._total_analyses}
