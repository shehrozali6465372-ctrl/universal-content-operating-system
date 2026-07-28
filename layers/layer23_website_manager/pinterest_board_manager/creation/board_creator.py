"""BoardCreator — AI-powered board naming and creation engine."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_board_manager.models.pinterest_board import PinterestBoard
from layers.layer23_website_manager.pinterest_board_manager.exceptions import BoardCreationError


class BoardCreator:
    """AI-powered board creation — auto-generates board name, description, and keywords from topic/niche."""

    # AI naming templates by niche
    NAMING_TEMPLATES: Dict[str, List[str]] = {
        "home_decor": [
            "{keyword} Ideas for a Modern Home",
            "Best {keyword} Inspiration",
            "{keyword} | Interior Design Ideas",
            "Creative {keyword} You'll Love",
            "{keyword} — Home Decor Collection",
        ],
        "fashion": [
            "Trendy {keyword} Ideas",
            "{keyword} Style Guide",
            "Best {keyword} Outfits",
            "{keyword} Fashion Inspiration",
            "Chic {keyword} Looks",
        ],
        "beauty": [
            "Best {keyword} Tips & Tricks",
            "{keyword} Beauty Ideas",
            "{keyword} Tutorials & Looks",
            "Amazing {keyword} Inspiration",
            "{keyword} Skincare & Makeup",
        ],
        "food": [
            "Delicious {keyword} Recipes",
            "Best {keyword} Ideas",
            "{keyword} | Easy Recipes",
            "{keyword} Food Inspiration",
            "Healthy {keyword} Meals",
        ],
        "fitness": [
            "Effective {keyword} Workouts",
            "{keyword} Fitness Tips",
            "Best {keyword} Exercises",
            "{keyword} Health & Wellness",
            "Transform with {keyword}",
        ],
        "travel": [
            "Best {keyword} Travel Guide",
            "{keyword} Destinations",
            "{keyword} Travel Inspiration",
            "Explore {keyword}",
            "{keyword} | Wanderlust",
        ],
        "tech": [
            "{keyword} Tech Trends",
            "Best {keyword} Innovations",
            "{keyword} Technology Guide",
            "Future of {keyword}",
            "{keyword} | Digital World",
        ],
        "finance": [
            "Smart {keyword} Tips",
            "{keyword} Money Guide",
            "Best {keyword} Strategies",
            "{keyword} Financial Freedom",
            "{keyword} Wealth Building",
        ],
        "DIY": [
            "Creative {keyword} DIY Projects",
            "Easy {keyword} Tutorials",
            "{keyword} Craft Ideas",
            "DIY {keyword} You Can Make",
            "{keyword} Step by Step",
        ],
    }

    DEFAULT_TEMPLATES = [
        "Best {keyword} Ideas",
        "{keyword} Inspiration",
        "{keyword} Collection",
        "Amazing {keyword}",
        "{keyword} You'll Love",
    ]

    DESCRIPTION_TEMPLATES = [
        "Discover the best {keyword} ideas and inspiration. From {niche}, find top {keyword} content curated just for you.",
        "Explore amazing {keyword} content. Get inspired with our curated collection of the best {keyword} in {niche}.",
        "Your ultimate source for {keyword} inspiration. Browse our collection and save your favorite {keyword} ideas.",
    ]

    def __init__(self) -> None:
        self._creation_log: List[dict] = []

    def generate_board_name(self, keyword: str, niche: str = "") -> str:
        """AI-generate an optimized board name from a keyword/niche."""
        niche_key = niche.lower().replace(" ", "_") if niche else ""
        templates = self.NAMING_TEMPLATES.get(niche_key, self.DEFAULT_TEMPLATES)

        import random
        template = random.choice(templates)
        return template.replace("{keyword}", keyword.strip().title()).replace("{niche}", niche or niche_key.replace("_", " "))

    def generate_description(self, keyword: str, niche: str = "") -> str:
        """Generate an SEO-optimized board description."""
        import random
        template = random.choice(self.DESCRIPTION_TEMPLATES)
        return template.replace("{keyword}", keyword).replace("{niche}", niche or "home decor")

    def generate_keywords(self, keyword: str, niche: str = "") -> List[str]:
        """Generate relevant keywords for a board."""
        base_keywords = [keyword, f"{keyword} ideas", f"{keyword} inspiration", f"best {keyword}"]
        if niche:
            base_keywords.extend([f"{niche} {keyword}", f"{keyword} for {niche}"])
        return list(set(base_keywords))

    def create_board_suggestion(self, keyword: str, niche: str = "", category: str = "other") -> Dict[str, Any]:
        """Generate a complete board suggestion (name, description, keywords)."""
        board_name = self.generate_board_name(keyword, niche)
        description = self.generate_description(keyword, niche)
        keywords = self.generate_keywords(keyword, niche)

        suggestion = {
            "board_name": board_name,
            "description": description,
            "keywords": keywords,
            "niche": niche or self._detect_niche(keyword),
            "category": category,
            "ai_generated": True,
        }

        self._creation_log.append({
            "keyword": keyword,
            "niche": niche,
            "generated_name": board_name,
            "timestamp": time.time(),
        })

        return suggestion

    def get_stats(self) -> Dict[str, Any]:
        return {"total_suggestions": len(self._creation_log)}

    @staticmethod
    def _detect_niche(text: str) -> str:
        t = text.lower()
        if any(w in t for w in ["home", "decor", "room", "kitchen", "bedroom", "furniture"]):
            return "home_decor"
        if any(w in t for w in ["fashion", "style", "outfit", "wear"]):
            return "fashion"
        if any(w in t for w in ["beauty", "makeup", "skincare", "cosmetic"]):
            return "beauty"
        if any(w in t for w in ["recipe", "food", "cooking", "baking", "meal"]):
            return "food"
        if any(w in t for w in ["fitness", "workout", "exercise", "gym", "yoga"]):
            return "fitness"
        if any(w in t for w in ["travel", "vacation", "trip", "destination"]):
            return "travel"
        if any(w in t for w in ["tech", "ai", "software", "digital", "gadget"]):
            return "tech"
        if any(w in t for w in ["finance", "money", "invest", "budget", "wealth"]):
            return "finance"
        if any(w in t for w in ["diy", "craft", "tutorial", "how to"]):
            return "DIY"
        return "other"
