"""ContentClassifier — Automatically detect niche, category, intent, audience, content type."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.content_mapping_engine.models.content_mapping import (
    ContentCategory, ContentIntent,
)
from layers.layer23_website_manager.content_mapping_engine.exceptions import ContentClassificationError


# Niche keyword maps
NICHE_KEYWORDS: Dict[str, List[str]] = {
    "home_decor": ["home", "decor", "bedroom", "kitchen", "living room", "bathroom",
                    "furniture", "interior", "design", "renovation", "organization",
                    "diy home", "wall art", "lighting", "curtain", "rug", "shelf"],
    "fashion": ["fashion", "outfit", "style", "wear", "dress", "shoes", "accessories",
                 "trendy", "wardrobe", "clothing", "jeans", "jacket", "bag", "jewelry"],
    "beauty": ["beauty", "skincare", "makeup", "hair", "cosmetic", "nail", "facial",
                "moisturizer", "serum", "lipstick", "eyeshadow", "foundation"],
    "food": ["recipe", "food", "cooking", "baking", "dinner", "breakfast", "dessert",
              "healthy meal", "smoothie", "snack", "salad", "soup", "chicken"],
    "tech": ["tech", "gadget", "software", "app", "phone", "laptop", "AI", "digital",
              "programming", "device", "smartphone", "computer", "internet"],
    "fitness": ["fitness", "workout", "exercise", "yoga", "gym", "weight loss",
                 "muscle", "cardio", "strength", "stretching", "pilates"],
    "travel": ["travel", "destination", "vacation", "hotel", "flight", "trip",
                "tourist", "adventure", "backpacking", "road trip", "beach"],
    "finance": ["finance", "money", "invest", "saving", "budget", "credit", "debt",
                 "tax", "retirement", "passive income", "crypto", "stock"],
    "diy": ["diy", "craft", "handmade", "tutorial", "woodworking", "sewing",
             "recycling", "upcycle", "homemade", "repair", "build"],
}


class ContentClassifier:
    """Classify content by niche, category, intent, audience, and content type."""

    def __init__(self) -> None:
        self._classification_log: List[dict] = []

    def classify(self, title: str, content: str = "", keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """Classify content and return niche, category, intent, audience, confidence."""
        if not title and not content:
            raise ContentClassificationError("Title or content required for classification")

        niche, confidence = self._detect_niche(title, content, keywords or [])
        category = self._map_niche_to_category(niche)
        intent = self._detect_intent(title, content)
        audience = self._detect_audience(niche, category)
        content_type = self._detect_content_type(title, content)

        result = {
            "niche": niche,
            "category": category.value,
            "intent": intent.value,
            "audience": audience,
            "content_type": content_type,
            "confidence": round(confidence, 2),
        }

        self._classification_log.append(result)
        return result

    def _detect_niche(self, title: str, content: str, keywords: List[str]) -> tuple:
        """Detect niche from title, content, and keywords."""
        text = (title + " " + content + " " + " ".join(keywords)).lower()
        scores: Dict[str, int] = {}

        for niche, kws in NICHE_KEYWORDS.items():
            score = 0
            for kw in kws:
                if kw in text:
                    score += 1
            if score > 0:
                scores[niche] = score

        if not scores:
            return "general", 0.3

        best = max(scores, key=scores.get)
        max_score = scores[best]
        total_keywords = len(NICHE_KEYWORDS.get(best, []))
        confidence = min(max_score / max(total_keywords, 1), 1.0)
        return best, confidence

    def _map_niche_to_category(self, niche: str) -> ContentCategory:
        mapping = {
            "home_decor": ContentCategory.HOME_DECOR,
            "fashion": ContentCategory.FASHION,
            "beauty": ContentCategory.BEAUTY,
            "food": ContentCategory.FOOD,
            "tech": ContentCategory.TECH,
            "fitness": ContentCategory.FITNESS,
            "travel": ContentCategory.TRAVEL,
            "finance": ContentCategory.FINANCE,
            "diy": ContentCategory.DIY,
        }
        return mapping.get(niche, ContentCategory.OTHER)

    def _detect_intent(self, title: str, content: str) -> ContentIntent:
        text = (title + " " + content).lower()
        if any(w in text for w in ["how to", "guide", "tutorial", "tips", "step", "learn"]):
            return ContentIntent.EDUCATIONAL
        if any(w in text for w in ["best", "top", "ideas", "inspiration", "beautiful", "amazing"]):
            return ContentIntent.INSPIRATIONAL
        if any(w in text for w in ["buy", "shop", "price", "deal", "offer", "review", "affordable"]):
            return ContentIntent.COMMERCIAL
        if any(w in text for w in ["fun", "entertaining", "hilarious", "interesting"]):
            return ContentIntent.ENTERTAINMENT
        return ContentIntent.INFORMATIONAL

    def _detect_audience(self, niche: str, category: ContentCategory) -> str:
        audience_map = {
            "home_decor": "homeowners",
            "fashion": "fashion enthusiasts",
            "beauty": "beauty conscious",
            "food": "food lovers",
            "tech": "tech enthusiasts",
            "fitness": "fitness enthusiasts",
            "travel": "travelers",
            "finance": "investors",
            "diy": "creatives",
        }
        return audience_map.get(niche, "general audience")

    def _detect_content_type(self, title: str, content: str) -> str:
        title_lower = title.lower()
        if any(w in title_lower for w in ["how", "guide", "tutorial"]):
            return "tutorial"
        if any(w in title_lower for w in ["list", "top", "best", "ideas", "ways"]):
            return "listicle"
        if any(w in title_lower for w in ["review", "vs", "comparison"]):
            return "review"
        if any(w in title_lower for w in ["recipe", "cook"]):
            return "recipe"
        return "article"

    def get_stats(self) -> Dict[str, Any]:
        niches: Dict[str, int] = {}
        for entry in self._classification_log:
            n = entry["niche"]
            niches[n] = niches.get(n, 0) + 1
        return {
            "total_classified": len(self._classification_log),
            "niches": niches,
        }
