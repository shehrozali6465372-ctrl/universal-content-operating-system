"""PinStrategyEngine — Decide pin type based on content, audience, and goals."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.content_mapping_engine.models.content_mapping import PinStrategy


class PinStrategyEngine:
    """Select the best pin strategy — standard, idea, carousel, product, rich, video."""

    def __init__(self) -> None:
        self._strategy_log: List[dict] = []

    def select_strategy(self, niche: str, intent: str, content_type: str,
                         has_multiple_images: bool = False) -> Dict[str, Any]:
        """Select best pin strategy based on content analysis."""
        strategy = PinStrategy.STANDARD
        reason = "Default strategy for general content"

        # Educational content → Idea Pin
        if intent == "educational" and content_type in ("tutorial", "recipe"):
            strategy = PinStrategy.IDEA_PIN
            reason = "Educational content performs best as Idea Pin"

        # Listicles → Carousel
        if content_type == "listicle" and has_multiple_images:
            strategy = PinStrategy.CAROUSEL
            reason = "Listicle with multiple images works well as Carousel"

        # Commercial intent → Product Pin
        if intent == "commercial":
            strategy = PinStrategy.PRODUCT_PIN
            reason = "Commercial content best suited for Product Pin"

        # Travel / Fashion → Rich Pin
        if niche in ("travel", "fashion") and intent == "inspirational":
            strategy = PinStrategy.RICH_PIN
            reason = "Inspirational content in travel/fashion benefits from Rich Pin"

        # Home decor → Standard (visual focus)
        if niche == "home_decor" and intent == "inspirational":
            strategy = PinStrategy.STANDARD
            reason = "Home decor visuals perform best as Standard Pins"

        result = {
            "strategy": strategy.value,
            "reason": reason,
        }

        self._strategy_log.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        strategies: Dict[str, int] = {}
        for entry in self._strategy_log:
            s = entry["strategy"]
            strategies[s] = strategies.get(s, 0) + 1
        return {
            "total_strategies": len(self._strategy_log),
            "by_strategy": strategies,
        }
