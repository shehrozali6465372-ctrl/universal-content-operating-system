"""SEOMapper — Generate SEO profile: keywords, long-tail, search intent, related topics."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.content_mapping_engine.exceptions import SEOMappingError


# Related topics by niche
RELATED_TOPICS: Dict[str, List[str]] = {
    "home_decor": ["interior design trends", "home renovation", "room makeover", "furniture shopping"],
    "fashion": ["seasonal trends", "capsule wardrobe", "style tips", "clothing care"],
    "beauty": ["skincare routine", "beauty hacks", "makeup trends", "hair care tips"],
    "food": ["meal prep", "healthy eating", "cooking techniques", "kitchen hacks"],
    "tech": ["tech reviews", "gadget comparisons", "software deals", "tech news"],
    "fitness": ["workout plans", "nutrition tips", "wellness", "recovery"],
    "travel": ["travel hacks", "budget travel", "destination guides", "packing tips"],
    "finance": ["personal finance", "investment tips", "saving strategies", "retirement planning"],
    "diy": ["home improvement", "craft projects", "upcycling ideas", "tool guides"],
    "garden": ["gardening tips", "plant care", "landscaping ideas", "seasonal gardening"],
}


class SEOMapper:
    """Generate comprehensive SEO profile for content."""

    def __init__(self) -> None:
        self._seo_log: List[dict] = []
        self._total_mapped = 0

    def generate_seo_profile(self, title: str, niche: str = "",
                               content: str = "",
                               keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate full SEO profile including keywords, long-tail, related topics."""
        if not title:
            raise SEOMappingError("Title is required for SEO mapping")

        keyword_list = self._extract_keywords(title, content, keywords or [])
        long_tail = self._generate_long_tail(title, keyword_list, niche)
        search_intent = self._detect_search_intent(title, niche)
        related = RELATED_TOPICS.get(niche, [])

        result = {
            "seo_keywords": keyword_list,
            "long_tail_keywords": long_tail,
            "search_intent": search_intent,
            "related_topics": related[:5],
        }

        self._seo_log.append(result)
        self._total_mapped += 1
        return result

    def _extract_keywords(self, title: str, content: str,
                           keywords: List[str]) -> List[str]:
        """Extract and merge keywords from multiple sources."""
        merged = list(keywords)

        # Extract from title
        words = title.lower().split()
        for w in words:
            cleaned = w.strip(",.!?;:()[]{}'\"").strip()
            if len(cleaned) > 3 and cleaned not in merged:
                merged.append(cleaned)

        # Extract from content
        if content:
            content_words = content.lower().split()[:50]
            for w in content_words:
                cleaned = w.strip(",.!?;:()[]{}'\"").strip()
                if len(cleaned) > 4 and cleaned not in merged:
                    merged.append(cleaned)

        return merged[:15]

    def _generate_long_tail(self, title: str, keywords: List[str],
                             niche: str) -> List[str]:
        """Generate long-tail keyword variations."""
        long_tail = []

        # Pattern-based generation
        patterns = [
            f"best {title.lower()}",
            f"{title.lower()} ideas",
            f"how to {title.lower()}",
            f"{title.lower()} for beginners",
            f"affordable {title.lower()}",
        ]

        for p in patterns:
            if len(p.split()) >= 3:
                long_tail.append(p[:80])

        # Add niche context
        if niche:
            niche_name = niche.replace("_", " ")
            long_tail.append(f"{title.lower()} in {niche_name}")

        return long_tail[:5]

    def _detect_search_intent(self, title: str, niche: str) -> str:
        """Detect search intent for SEO purposes."""
        t = title.lower()
        if any(w in t for w in ["buy", "price", "cost", "shop"]):
            return "transactional"
        if any(w in t for w in ["how", "guide", "tutorial", "tips"]):
            return "how-to"
        if any(w in t for w in ["best", "top", "vs", "review"]):
            return "commercial"
        if any(w in t for w in ["what", "why", "when", "define"]):
            return "informational"
        return "inspirational"

    def get_stats(self) -> Dict[str, Any]:
        return {"total_seo_profiles": self._total_mapped}
