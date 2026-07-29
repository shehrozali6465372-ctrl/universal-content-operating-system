"""SEOMapper — Generate keywords, long-tail keywords, search intent, and related topics."""
from __future__ import annotations
import random
from typing import Any, Dict, List, Optional


class SEOMapper:
    """Generate SEO profile for mapped content — keywords, long-tail, intent, related topics."""

    NICHE_KEYWORD_MAP: Dict[str, Dict[str, Any]] = {
        "home_decor": {
            "keywords": ["interior design", "home decor", "room ideas", "furniture"],
            "long_tail": ["small bedroom ideas on a budget", "modern living room decor 2026"],
            "related_topics": ["color schemes", "organization tips", "DIY furniture"],
        },
        "fashion": {
            "keywords": ["fashion trends", "outfit ideas", "style guide"],
            "long_tail": ["casual outfit ideas for women", "winter fashion trends 2026"],
            "related_topics": ["accessories", "seasonal fashion", "wardrobe essentials"],
        },
        "beauty": {
            "keywords": ["skincare routine", "makeup tips", "beauty products"],
            "long_tail": ["best skincare routine for dry skin", "natural makeup tutorial"],
            "related_topics": ["hair care", "nail art", "beauty hacks"],
        },
        "food": {
            "keywords": ["easy recipes", "cooking tips", "healthy meals"],
            "long_tail": ["quick 30-minute dinner recipes", "healthy breakfast ideas for weight loss"],
            "related_topics": ["meal prep", "baking", "smoothie recipes"],
        },
        "tech": {
            "keywords": ["tech gadgets", "software reviews", "digital tools"],
            "long_tail": ["best budget smartphones 2026", "AI tools for productivity"],
            "related_topics": ["mobile apps", "smart home", "cybersecurity"],
        },
        "fitness": {
            "keywords": ["workout plans", "fitness tips", "exercise routines"],
            "long_tail": ["30-day fitness challenge for beginners", "home workout without equipment"],
            "related_topics": ["yoga", "nutrition", "weight training"],
        },
        "travel": {
            "keywords": ["travel destinations", "vacation ideas", "budget travel"],
            "long_tail": ["best budget travel destinations 2026", "solo travel tips for women"],
            "related_topics": ["hotel deals", "travel gear", "road trips"],
        },
        "finance": {
            "keywords": ["personal finance", "investing tips", "money management"],
            "long_tail": ["passive income ideas for beginners", "how to save money monthly"],
            "related_topics": ["crypto", "retirement", "budgeting"],
        },
        "diy": {
            "keywords": ["DIY projects", "home improvement", "craft ideas"],
            "long_tail": ["DIY home decor projects for beginners", "easy crafts to sell"],
            "related_topics": ["woodworking", "upcycling", "sewing"],
        },
    }

    SEARCH_INTENT_MAP = {
        "educational": "how-to, tutorial, guide",
        "inspirational": "ideas, inspiration, best",
        "commercial": "buy, price, review, best",
        "informational": "what is, why, guide",
        "entertainment": "fun, interesting, amazing",
    }

    def __init__(self) -> None:
        self._seo_log: List[dict] = []

    def generate_seo_profile(self, niche: str, intent: str, title: str = "") -> Dict[str, Any]:
        """Generate complete SEO profile for content."""
        data = self.NICHE_KEYWORD_MAP.get(niche, {
            "keywords": ["general"],
            "long_tail": ["general topic guide"],
            "related_topics": ["related ideas"],
        })

        keywords = list(data["keywords"])
        long_tail = list(data["long_tail"])
        related = list(data["related_topics"])

        # Incorporate title words into keywords
        if title:
            title_words = [w.lower() for w in title.split() if len(w) > 3][:3]
            for w in title_words:
                if w not in keywords:
                    keywords.append(w)

        profile = {
            "keywords": keywords[:10],
            "long_tail_keywords": long_tail[:5],
            "search_intent": self.SEARCH_INTENT_MAP.get(intent, "informational"),
            "related_topics": related[:5],
        }

        self._seo_log.append(profile)
        return profile

    def get_stats(self) -> Dict[str, Any]:
        return {"total_profiles": len(self._seo_log)}
