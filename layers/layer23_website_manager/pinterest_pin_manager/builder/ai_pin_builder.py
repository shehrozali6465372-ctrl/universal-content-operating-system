"""AIPinBuilder — AI-powered pin content generation from articles/ideas."""
from __future__ import annotations
import random
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_pin_manager.models.pinterest_pin import PinterestPin, PinType


class AIPinBuilder:
    """AI-powered pin content creation — generates title, description, alt text, CTA from articles."""

    # CTA templates by content type
    CTA_TEMPLATES: Dict[str, List[str]] = {
        "article": [
            "Read the full article on our website",
            "Click to learn more",
            "Get the complete guide",
            "Read more",
            "Discover more",
        ],
        "product": [
            "Shop now",
            "Get yours today",
            "Buy now",
            "Limited offer — shop now",
            "Check price",
        ],
        "idea": [
            "Save for later",
            "Get inspired",
            "Try this idea",
            "Pin to your board",
            "Share with friends",
        ],
    }

    TITLE_TEMPLATES = [
        "{title} That Will Inspire You",
        "{title} | Must-See Ideas",
        "10 {title} You Need to See",
        "The Best {title} Collection",
        "{title} — Complete Guide",
        "Stunning {title} Ideas",
        "Amazing {title} to Try Today",
        "{title} Everyone Is Talking About",
    ]

    def __init__(self) -> None:
        self._build_log: List[dict] = []

    def build_from_article(self, article_title: str, article_content: str = "",
                            niche: str = "", keywords: Optional[List[str]] = None,
                            pin_type: PinType = PinType.ARTICLE) -> Dict[str, Any]:
        """Generate complete pin content from an article."""
        pin_title = self._generate_title(article_title, niche)
        description = self._generate_description(article_title, article_content, keywords)
        alt_text = self._generate_alt_text(article_title)
        cta = self._get_cta(pin_type)

        result = {
            "pin_title": pin_title,
            "pin_description": description,
            "alt_text": alt_text,
            "call_to_action": cta,
            "hashtags": self._generate_hashtags(niche, keywords or []),
            "seo_keywords": self._extract_keywords(article_title, article_content, keywords),
            "search_intent": self._detect_intent(article_title),
        }

        self._build_log.append({
            "article_title": article_title,
            "generated_title": pin_title,
        })

        return result

    def _generate_title(self, article_title: str, niche: str = "") -> str:
        """Generate an SEO-optimized pin title from article."""
        template = random.choice(self.TITLE_TEMPLATES)
        title = template.replace("{title}", article_title.strip())

        # Add niche context
        if niche and niche.lower().replace(" ", "_") not in title.lower():
            niche_title = niche.replace("_", " ").title()
            title = f"{title} — {niche_title}"

        return title[:100]  # Pinterest max 100 chars

    def _generate_description(self, title: str, content: str = "",
                               keywords: Optional[List[str]] = None) -> str:
        """Generate pin description with keywords."""
        desc = content[:400] if content else f"Discover amazing {title.lower()} ideas and inspiration."
        if keywords:
            kw_str = ", ".join(keywords[:5])
            if kw_str.lower() not in desc.lower():
                desc = f"{desc}\n\nKeywords: {kw_str}"
        return desc[:500]

    def _generate_alt_text(self, title: str) -> str:
        """Generate image alt text."""
        return f"{title} — Pinterest pin image"

    def _get_cta(self, pin_type: PinType) -> str:
        templates = self.CTA_TEMPLATES.get(pin_type.value, self.CTA_TEMPLATES["article"])
        return random.choice(templates)

    def _generate_hashtags(self, niche: str = "", keywords: Optional[List[str]] = None) -> List[str]:
        tags = set()
        if niche:
            n = niche.lower().replace(" ", "")
            tags.add(f"#{n}")
            tags.add(f"#{n}ideas")
        if keywords:
            for kw in keywords[:5]:
                k = kw.lower().replace(" ", "")
                if k:
                    tags.add(f"#{k}")
        return list(tags)[:10]

    def _extract_keywords(self, title: str, content: str = "",
                           keywords: Optional[List[str]] = None) -> List[str]:
        result = list(keywords or [])
        words = title.lower().split()
        for w in words[:5]:
            if len(w) > 3 and w not in result:
                result.append(w)
        return result[:10]

    def _detect_intent(self, title: str) -> str:
        t = title.lower()
        if any(w in t for w in ["how", "guide", "tutorial", "tips", "step"]):
            return "educational"
        if any(w in t for w in ["best", "top", "ideas", "collection", "inspiration"]):
            return "inspirational"
        if any(w in t for w in ["buy", "shop", "price", "deal", "offer"]):
            return "commercial"
        return "informational"

    def get_stats(self) -> Dict[str, Any]:
        return {"total_generated": len(self._build_log)}
