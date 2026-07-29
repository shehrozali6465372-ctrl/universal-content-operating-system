"""PinSEOManager — Pinterest SEO for pins: titles, descriptions, keywords, rich pin metadata."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_pin_manager.models.pinterest_pin import PinterestPin


class PinSEOManager:
    """Pinterest SEO optimization for pins — search intent, keywords, rich metadata."""

    def __init__(self) -> None:
        self._seo_log: List[dict] = []

    def optimize_pin(self, pin: PinterestPin) -> Dict[str, Any]:
        """Run full SEO optimization on a pin."""
        # Title optimization
        if not pin.seo_title:
            pin.seo_title = pin.pin_title

        # Ensure keywords
        if not pin.seo_keywords:
            pin.seo_keywords = self._extract_keywords(pin.pin_title)

        # Ensure hashtags
        if not pin.hashtags:
            pin.hashtags = self._generate_hashtags(pin.seo_keywords, pin.niche)

        # SEO score
        pin.seo_score = self.calculate_score(pin)

        result = {
            "seo_score": pin.seo_score,
            "title": pin.seo_title,
            "keyword_count": len(pin.seo_keywords),
            "hashtag_count": len(pin.hashtags),
        }

        self._seo_log.append(result)
        return result

    def calculate_score(self, pin: PinterestPin) -> float:
        """Calculate SEO score (0-100) for a pin."""
        score = 100.0

        if not pin.pin_title:
            score -= 30
        elif len(pin.pin_title) < 10:
            score -= 15
        elif len(pin.pin_title) > 100:
            score -= 5

        if not pin.pin_description:
            score -= 25
        elif len(pin.pin_description) < 50:
            score -= 10

        if not pin.seo_keywords:
            score -= 20
        elif len(pin.seo_keywords) < 3:
            score -= 10

        if not pin.hashtags:
            score -= 10

        if not pin.website_url:
            score -= 10

        if not pin.image_path and not pin.image_url:
            score -= 15

        if pin.alt_text:
            score += 5

        return max(0, min(100, score))

    def _extract_keywords(self, title: str) -> List[str]:
        words = title.lower().split()[:8]
        return [w for w in words if len(w) > 2]

    def _generate_hashtags(self, keywords: List[str], niche: str = "") -> List[str]:
        tags = set()
        if niche:
            tags.add(f"#{niche.lower().replace(' ', '')}")
        for kw in keywords[:5]:
            clean = kw.lower().replace(" ", "")
            if clean:
                tags.add(f"#{clean}")
        return list(tags)[:10]

    def generate_rich_pin_metadata(self, pin: PinterestPin, article_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate rich pin metadata for article/product pins."""
        metadata = {
            "title": pin.seo_title or pin.pin_title,
            "description": pin.pin_description[:200] if pin.pin_description else "",
            "url": pin.website_url,
        }

        if article_data:
            metadata.update({
                "author": article_data.get("author", ""),
                "date_published": article_data.get("date_published", ""),
                "site_name": article_data.get("site_name", ""),
            })

        pin.rich_pin_data = metadata
        pin.is_rich_pin = True
        return metadata

    def get_stats(self) -> Dict[str, Any]:
        return {"total_optimizations": len(self._seo_log)}
