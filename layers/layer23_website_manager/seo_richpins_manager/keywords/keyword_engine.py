"""KeywordEngine — Generate primary, secondary, long-tail, LSI keywords with search intent."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.seo_richpins_manager.exceptions import KeywordGenerationError


# Niche keyword banks
NICHE_KEYWORD_BANK: Dict[str, Dict[str, Any]] = {
    "home_decor": {
        "primary": ["home decor ideas", "interior design", "room decor"],
        "secondary": ["modern home", "decorating tips", "home styling", "wall art", "furniture"],
        "long_tail": ["small living room decor ideas on a budget", "modern bedroom design trends 2026"],
        "lsi": ["paint colors", "furniture layout", "lighting design", "window treatments"],
    },
    "fashion": {
        "primary": ["fashion trends", "outfit ideas", "style guide"],
        "secondary": ["wardrobe essentials", "seasonal fashion", "accessories", "street style"],
        "long_tail": ["casual outfit ideas for women over 40", "winter fashion trends 2026"],
        "lsi": ["color matching", "fabric types", "body types", "dress codes"],
    },
    "beauty": {
        "primary": ["beauty tips", "skincare routine", "makeup tutorial"],
        "secondary": ["anti-aging", "natural beauty", "hair care", "nail art"],
        "long_tail": ["best skincare routine for dry skin", "natural makeup for beginners"],
        "lsi": ["skin types", "beauty tools", "ingredients", "SPF protection"],
    },
    "food": {
        "primary": ["easy recipes", "cooking tips", "healthy meals"],
        "secondary": ["meal prep", "baking", "smoothies", "dinner ideas"],
        "long_tail": ["30-minute dinner recipes for busy weeknights", "healthy breakfast for weight loss"],
        "lsi": ["nutrition facts", "cooking methods", "kitchen tools", "meal planning"],
    },
    "tech": {
        "primary": ["tech reviews", "gadget guide", "software tools"],
        "secondary": ["smart home", "mobile apps", "AI tools", "cybersecurity"],
        "long_tail": ["best budget smartphones under 500", "AI productivity tools for small business"],
        "lsi": ["specifications", "comparison", "user experience", "warranty"],
    },
    "fitness": {
        "primary": ["fitness tips", "workout routine", "exercise guide"],
        "secondary": ["weight loss", "muscle building", "yoga", "cardio"],
        "long_tail": ["30-day fitness challenge for beginners at home", "best exercises for lower belly fat"],
        "lsi": ["form and technique", "rest days", "protein intake", "hydration"],
    },
    "travel": {
        "primary": ["travel destinations", "vacation guide", "budget travel"],
        "secondary": ["solo travel", "family trips", "road trips", "luxury travel"],
        "long_tail": ["best budget travel destinations in Europe 2026", "solo female travel safety tips"],
        "lsi": ["travel insurance", "packing tips", "local cuisine", "cultural etiquette"],
    },
    "finance": {
        "primary": ["personal finance", "investing tips", "money management"],
        "secondary": ["saving money", "credit score", "passive income", "retirement"],
        "long_tail": ["passive income ideas for beginners with no money", "how to improve credit score fast"],
        "lsi": ["compound interest", "tax planning", "budgeting apps", "emergency fund"],
    },
    "diy": {
        "primary": ["DIY projects", "home improvement", "craft ideas"],
        "secondary": ["woodworking", "upcycling", "sewing", "garden DIY"],
        "long_tail": ["easy DIY home decor projects for beginners", "DIY furniture makeover ideas"],
        "lsi": ["tools needed", "safety tips", "materials", "step by step"],
    },
}


class KeywordEngine:
    """Generate complete keyword strategy — primary, secondary, long-tail, LSI, search intent."""

    def __init__(self) -> None:
        self._generation_log: List[dict] = []

    def generate_keywords(self, niche: str, title: str = "",
                           content: str = "") -> Dict[str, Any]:
        """Generate full keyword profile for a niche/topic."""
        bank = NICHE_KEYWORD_BANK.get(niche, NICHE_KEYWORD_BANK.get("home_decor"))

        primary = bank["primary"][0]
        secondary = list(bank["secondary"])
        long_tail = list(bank["long_tail"])
        lsi = list(bank["lsi"])

        # Add title words as secondary keywords
        if title:
            title_words = [w.lower() for w in title.split() if len(w) > 3][:5]
            for w in title_words:
                if w not in secondary:
                    secondary.append(w)

        intent = self._detect_intent(title, content)

        result = {
            "primary_keyword": primary,
            "secondary_keywords": secondary[:8],
            "long_tail_keywords": long_tail[:4],
            "lsi_keywords": lsi[:6],
            "search_intent": intent,
        }

        self._generation_log.append(result)
        return result

    def _detect_intent(self, title: str, content: str) -> str:
        text = (title + " " + content).lower()
        if any(w in text for w in ["how to", "guide", "tutorial", "tips", "step"]):
            return "educational"
        if any(w in text for w in ["best", "top", "ideas", "inspiration"]):
            return "inspirational"
        if any(w in text for w in ["buy", "shop", "price", "deal", "review"]):
            return "commercial"
        return "informational"

    def get_stats(self) -> Dict[str, Any]:
        return {"total_generations": len(self._generation_log)}
