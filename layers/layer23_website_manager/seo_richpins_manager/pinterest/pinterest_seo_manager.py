"""PinterestSEOManager — Optimize pins for Pinterest search with keywords, hashtags, descriptions."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class PinterestSEOManager:
    """Generate Pinterest-optimized titles, descriptions, keywords, and hashtags."""

    def __init__(self) -> None:
        self._seo_log: List[dict] = []

    def optimize_pin(self, article_title: str, niche: str = "",
                      primary_keyword: str = "",
                      description: str = "") -> Dict[str, Any]:
        """Generate a complete Pinterest SEO profile for a pin."""
        # Pin title (max 100 chars)
        pin_title = article_title[:100]
        if primary_keyword and primary_keyword.lower() not in pin_title.lower():
            pin_title = f"{article_title[:70]} | {primary_keyword.title()}"
            pin_title = pin_title[:100]

        # Pin description (max 500 chars)
        pin_desc = description[:400] if description else f"Discover amazing {article_title.lower()}."
        if primary_keyword:
            pin_desc = f"{pin_desc}\n\nKeywords: {primary_keyword}"

        # Pinterest keywords
        keywords = [primary_keyword] if primary_keyword else []
        if niche:
            keywords.append(niche.replace("_", " "))
        keywords.extend([w for w in article_title.split() if len(w) > 3][:5])

        # Hashtags
        hashtags = []
        if niche:
            hashtags.append(f"#{niche.replace('_', '')}")
            hashtags.append(f"#{niche.replace('_', '')}ideas")
        for kw in keywords[:4]:
            clean = kw.lower().replace(" ", "")
            if clean:
                hashtags.append(f"#{clean}")

        result = {
            "pin_seo_title": pin_title[:100],
            "pin_description": pin_desc[:500],
            "pinterest_keywords": list(set(keywords))[:10],
            "pinterest_hashtags": list(set(hashtags))[:10],
        }

        self._seo_log.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {"total_optimizations": len(self._seo_log)}
