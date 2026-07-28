"""BoardRecommendationEngine — AI suggests new boards based on trends and gaps."""
from __future__ import annotations
import time
import random
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_board_manager.models.pinterest_board import PinterestBoard


class BoardRecommendationEngine:
    """AI-powered board recommendations — detect gaps, suggest new boards."""

    # High-traffic keyword clusters by niche
    TRENDING_KEYWORDS: Dict[str, List[str]] = {
        "home_decor": ["Minimalist", "Scandinavian", "Bohemian", "Farmhouse", "Industrial",
                        "Small Space", "Sustainable", "Vintage", "Modern", "Rustic"],
        "fashion": ["Capsule Wardrobe", "Street Style", "Sustainable Fashion", "Vintage",
                     "Minimalist", "Athleisure", "Seasonal", "Workwear", "Evening"],
        "beauty": ["Clean Beauty", "Skincare Routine", "Makeup Tutorial", "Natural",
                    "Anti Aging", "Hair Care", "Nail Art", "Beauty Tools"],
        "food": ["Quick Meals", "Healthy Recipes", "Meal Prep", "Baking", "Vegan",
                  "Keto", "Comfort Food", "International", "Desserts"],
        "fitness": ["Home Workout", "Yoga", "HIIT", "Strength Training", "Running",
                     "Stretching", "Weight Loss", "Mindfulness"],
        "travel": ["Budget Travel", "Solo Travel", "Road Trip", "Beach", "Mountain",
                    "City Guide", "Travel Tips", "Hidden Gems"],
        "tech": ["AI Tools", "Productivity", "Software", "Gadgets", "Coding",
                  "Tech News", "Digital Nomad", "Smart Home"],
    }

    def __init__(self) -> None:
        self._recommendation_log: List[dict] = []

    def recommend_boards(self, niche: str, existing_boards: List[PinterestBoard],
                          max_recommendations: int = 5) -> List[Dict[str, Any]]:
        """Recommend new boards based on trending keywords and existing gaps."""
        niche_key = niche.lower().replace(" ", "_")
        trending = self.TRENDING_KEYWORDS.get(niche_key, [])

        if not trending:
            return []

        # Find existing board names
        existing_names = [b.board_name.lower() for b in existing_boards if b.niche == niche]

        recommendations = []
        for keyword in trending:
            # Skip if similar board already exists
            keyword_lower = keyword.lower()
            if any(keyword_lower in name for name in existing_names):
                continue

            recommendations.append({
                "suggested_name": f"{keyword} {niche.title()} Ideas",
                "keyword": keyword,
                "niche": niche,
                "reason": f"Trending keyword with high search volume",
                "priority": "high" if len(recommendations) < 3 else "medium",
            })

            if len(recommendations) >= max_recommendations:
                break

        if recommendations:
            self._recommendation_log.append({
                "niche": niche,
                "recommendations": len(recommendations),
                "timestamp": time.time(),
            })

        return recommendations

    def detect_gaps(self, niche: str, existing_boards: List[PinterestBoard]) -> List[Dict[str, Any]]:
        """Detect gaps in board coverage for a niche."""
        niche_key = niche.lower().replace(" ", "_")
        trending = self.TRENDING_KEYWORDS.get(niche_key, [])

        existing_names = [b.board_name.lower() for b in existing_boards if b.niche == niche]
        gaps = []

        for keyword in trending:
            keyword_lower = keyword.lower()
            if not any(keyword_lower in name for name in existing_names):
                gaps.append({
                    "gap_keyword": keyword,
                    "suggested_board": f"{keyword} {niche.title()} Ideas",
                    "potential": "high",
                })

        return gaps

    def get_stats(self) -> Dict[str, Any]:
        return {"total_recommendations": len(self._recommendation_log)}
