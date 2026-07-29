"""ContentClassifier — AI-driven content analysis: niche, topic, category, intent, audience."""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.content_mapping_engine.models.content_mapping import (
    ContentMapping, ContentIntent, ContentAudience,
)
from layers.layer23_website_manager.content_mapping_engine.exceptions import ContentClassificationError


# Niche keyword maps
NICHE_KEYWORDS: Dict[str, List[str]] = {
    "home_decor": ["bedroom", "living room", "kitchen", "bathroom", "decor", "interior",
                    "furniture", "wall art", "lighting", "rug", "curtain", "sofa",
                    "dining", "shelf", "mirror", "plant", "vase", "cushion"],
    "fashion": ["outfit", "dress", "shoes", "bag", "jewelry", "style", "trend",
                 "wear", "fashion", "clothing", "accessory", "boots", "sneaker",
                 "handbag", "scarf", "coat", "jacket", "denim"],
    "beauty": ["skincare", "makeup", "hair", "nail", "beauty", "cosmetic", "lotion",
                "serum", "moisturizer", "lipstick", "eyeshadow", "foundation",
                "facial", "mask", "shampoo", "perfume"],
    "food": ["recipe", "cook", "bake", "dinner", "lunch", "breakfast", "dessert",
              "chicken", "pasta", "salad", "soup", "cake", "cookie", "smoothie",
              "vegetarian", "vegan", "grill", "roast"],
    "tech": ["gadget", "tech", "software", "app", "phone", "laptop", "computer",
              "device", "digital", "smartphone", "tablet", "wearable", "smartwatch",
              "headphone", "charger", "camera"],
    "fitness": ["workout", "exercise", "gym", "yoga", "fitness", "muscle", "cardio",
                 "weight", "pilates", "stretching", "run", "walk", "training",
                 "dumbbell", "resistance", "hiit"],
    "travel": ["travel", "vacation", "destination", "hotel", "flight", "trip",
                "tourist", "beach", "mountain", "city", "road trip", "backpack",
                "luggage", "passport", "adventure"],
    "finance": ["money", "save", "invest", "budget", "finance", "debt", "credit",
                 "loan", "mortgage", "tax", "retirement", "wealth", "stock",
                 "crypto", "bank", "insurance"],
    "DIY": ["diy", "craft", "make", "build", "wood", "paint", "sew", "knit",
             "recycle", "upcycle", "repair", "fix", "decorate", "homemade",
             "tool", "drill", "saw"],
    "garden": ["garden", "plant", "flower", "tree", "grass", "landscape", "yard",
                "patio", "vegetable", "herb", "seed", "soil", "pot", "watering",
                "prune", "compost"],
}

INTENT_KEYWORDS: Dict[str, List[str]] = {
    "educational": ["how to", "guide", "tutorial", "tips", "step", "learn", "technique",
                     "master", "complete guide", "beginners", "explain"],
    "inspirational": ["ideas", "inspiration", "best", "top", "amazing", "stunning",
                       "beautiful", "gorgeous", "collection", "favorite", "must see"],
    "commercial": ["buy", "shop", "price", "deal", "offer", "discount", "sale",
                    "best price", "affordable", "cheap", "review", "vs"],
    "entertainment": ["fun", "funny", "game", "quiz", "challenge", "entertaining",
                       "humor", "joke", "comedy"],
}

AUDIENCE_KEYWORDS: Dict[str, List[str]] = {
    "women": ["women", "woman", "female", "her", "she", "lady", "girl", "mom",
               "mother", "bridal", "wedding", "beauty", "fashion"],
    "men": ["men", "man", "male", "him", "he", "guy", "gentleman", "groom",
             "beard", "shaving"],
    "parents": ["parent", "kid", "child", "baby", "toddler", "family", "mom",
                 "dad", "children", "school"],
    "professionals": ["professional", "office", "career", "business", "work",
                       "entrepreneur", "startup", "executive", "corporate"],
    "students": ["student", "college", "study", "exam", "dorm", "school",
                  "university", "classroom"],
    "homeowners": ["homeowner", "house", "home", "property", "mortgage", "renovation",
                    "repair", "maintenance"],
}


class ContentClassifier:
    """Analyze article content to detect niche, category, intent, audience."""

    def __init__(self) -> None:
        self._classification_log: List[dict] = []
        self._total_classified = 0

    def classify(self, title: str, content: str = "",
                 keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """Full classification of article content."""
        if not title:
            raise ContentClassificationError("Title is required for classification")

        niche = self._detect_niche(title, content, keywords or [])
        category = self._detect_category(title, niche)
        subcategory = self._detect_subcategory(title, niche, category)
        intent = self._detect_intent(title, content)
        audience = self._detect_audience(title, content)
        confidence = self._calculate_confidence(title, niche, intent)
        topic = self._extract_topic(title)
        content_type = self._detect_content_type(title, content)

        result = {
            "niche": niche,
            "category": category,
            "subcategory": subcategory,
            "topic": topic,
            "intent": intent.value,
            "audience": audience.value,
            "content_type": content_type,
            "confidence": round(confidence, 2),
        }

        self._classification_log.append(result)
        self._total_classified += 1
        return result

    def _detect_niche(self, title: str, content: str, keywords: List[str]) -> str:
        """Detect niche from title, content, and keywords."""
        text = f"{title} {content}".lower()
        scores: Dict[str, int] = {}

        for niche, kw_list in NICHE_KEYWORDS.items():
            score = 0
            for kw in kw_list:
                if kw.lower() in text:
                    score += 2
            for kw in keywords:
                if kw.lower() in title.lower():
                    score += 3
                if kw.lower() in content.lower():
                    score += 1
            if score > 0:
                scores[niche] = score

        if not scores:
            return "general"

        return max(scores, key=scores.get)

    def _detect_category(self, title: str, niche: str) -> str:
        """Detect category within a niche."""
        t = title.lower()
        niche_categories = {
            "home_decor": ["bedroom", "living room", "kitchen", "bathroom", "dining",
                           "office", "outdoor", "lighting", "wall art", "storage"],
            "fashion": ["dresses", "shoes", "bags", "jewelry", "outerwear",
                         "activewear", "formal", "casual", "seasonal"],
            "beauty": ["skincare", "makeup", "hair care", "nails", "fragrance",
                        "bath", "tools"],
            "food": ["desserts", "main course", "appetizers", "breakfast",
                      "drinks", "salads", "soups", "baking"],
            "tech": ["smartphones", "laptops", "audio", "wearables", "gaming",
                      "cameras", "smart home"],
        }

        cats = niche_categories.get(niche, [niche])
        for cat in cats:
            if cat.lower() in t:
                return cat
        return niche.replace("_", " ").title()

    def _detect_subcategory(self, title: str, niche: str, category: str) -> str:
        """Detect a more specific subcategory."""
        t = title.lower()
        # Common subcategories
        subs = ["small", "modern", "minimalist", "rustic", "vintage", "luxury",
                "budget", "diy", "organic", "vegan", "gluten-free", "quick",
                "easy", "beginner", "advanced", "kids", "pet", "eco-friendly"]
        for sub in subs:
            if sub in t:
                return sub
        return "general"

    def _detect_intent(self, title: str, content: str) -> ContentIntent:
        """Detect content intent from title and content."""
        text = f"{title} {content}".lower()

        for intent, keywords in INTENT_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    return ContentIntent(intent)

        return ContentIntent.INFORMATIONAL

    def _detect_audience(self, title: str, content: str) -> ContentAudience:
        """Detect target audience."""
        text = f"{title} {content}".lower()

        for audience, keywords in AUDIENCE_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    return ContentAudience(audience)

        return ContentAudience.ALL

    def _extract_topic(self, title: str) -> str:
        """Extract main topic from title."""
        cleaned = re.sub(r'[\d]+\s+', '', title)
        cleaned = re.sub(r'\b(ideas|tips|ways|how to|best|top|amazing|simple|easy)\b',
                         '', cleaned, flags=re.IGNORECASE)
        return cleaned.strip().strip('-').strip()[:80]

    def _detect_content_type(self, title: str, content: str) -> str:
        """Detect if content is list, guide, review, etc."""
        t = title.lower()
        if any(w in t for w in ["list", "ways", "ideas", "tips", "top", "best"]):
            return "list"
        if any(w in t for w in ["how to", "guide", "tutorial"]):
            return "guide"
        if any(w in t for w in ["review", "vs"]):
            return "review"
        if any(w in t for w in ["recipe"]):
            return "recipe"
        return "article"

    def _calculate_confidence(self, title: str, niche: str, intent: ContentIntent) -> float:
        """Calculate AI confidence score for classification."""
        score = 0.7  # base
        if niche != "general":
            score += 0.15
        if intent != ContentIntent.INFORMATIONAL:
            score += 0.1
        if len(title) > 20:
            score += 0.05
        return min(1.0, score)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_classified": self._total_classified,
            "recent_logs": self._classification_log[-10:],
        }
