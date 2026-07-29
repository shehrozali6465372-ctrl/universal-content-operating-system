"""TrafficOptimizer — AI recommendations for better pins, boards, keywords, publish times."""
from __future__ import annotations
import random
from typing import Any, Dict, List, Optional


class TrafficOptimizer:
    """Analyze traffic data and recommend optimizations."""

    RECOMMENDATIONS = [
        "Publish during peak hours (2-4 PM EST) for maximum Pinterest engagement",
        "Use vertical images (1000x1500) for better Pinterest CTR",
        "Add more keywords to pin descriptions for search visibility",
        "Create more listicle-style content for higher click-through rates",
        "Optimize for mobile — 80% of Pinterest traffic is mobile",
        "Use rich pins with article metadata for better visibility",
        "Post consistently — 3-5 pins per day per account",
        "Leverage seasonal trends in your niche for traffic spikes",
        "Create video pins — they get 4x more engagement",
        "Join group boards for wider reach",
    ]

    def __init__(self) -> None:
        self._optimization_log: List[dict] = []

    def analyze_traffic(self, source_breakdown: Dict[str, int],
                         top_pages: Optional[List[Any]] = None,
                         top_pins: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Analyze traffic patterns and suggest optimizations."""
        suggestions = []
        total = sum(source_breakdown.values()) if source_breakdown else 0

        if total > 0:
            # Check source diversity
            if len(source_breakdown) <= 2:
                suggestions.append("Low traffic source diversity. Expand to more channels.")

            # Check Pinterest dominance
            pinterest_pct = (source_breakdown.get("Pinterest", 0) / total) * 100 if total > 0 else 0
            if pinterest_pct > 80:
                suggestions.append(f"Pinterest is {pinterest_pct:.0f}% of traffic. Diversify to Google Search and Direct.")
            elif pinterest_pct < 20:
                suggestions.append("Pinterest traffic is low. Optimize pins for better reach.")

        # General recommendations
        suggestions.extend(random.sample(self.RECOMMENDATIONS, min(3, len(self.RECOMMENDATIONS))))

        result = {"suggestions": suggestions, "suggestion_count": len(suggestions)}
        self._optimization_log.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {"total_analyses": len(self._optimization_log)}
