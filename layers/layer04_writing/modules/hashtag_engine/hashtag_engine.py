"""Hashtag & Keyword Engine — Platform-specific hashtags and SEO keywords."""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional


PLATFORM_HASHTAG_LIMITS = {
    "facebook": 5, "instagram": 30, "twitter": 3, "linkedin": 5,
    "tiktok": 8, "youtube": 15, "pinterest": 10, "threads": 5,
}

CATEGORY_HASHTAGS = {
    "technology": ["#AI", "#Tech", "#Innovation", "#Digital", "#Future", "#Coding", "#DataScience"],
    "finance": ["#Finance", "#Crypto", "#Investing", "#StockMarket", "#Bitcoin", "#Wealth"],
    "health": ["#Health", "#Fitness", "#Wellness", "#Nutrition", "#MentalHealth", "#Exercise"],
    "education": ["#Education", "#Learning", "#Students", "#StudyTips", "#Knowledge", "#OnlineLearning"],
    "business": ["#Business", "#Entrepreneur", "#Marketing", "#Startup", "#Growth", "#Leadership"],
    "lifestyle": ["#Lifestyle", "#Motivation", "#Inspiration", "#Daily", "#Life", "#Mindset"],
}


class HashtagResult:
    """Result of hashtag generation."""
    __slots__ = ("hashtags", "keywords", "platform", "count", "metadata")

    def __init__(self, platform: str = "facebook") -> None:
        self.hashtags: List[str] = []
        self.keywords: List[str] = []
        self.platform = platform
        self.count = 0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hashtags": self.hashtags,
            "keywords": self.keywords,
            "platform": self.platform,
            "count": self.count,
        }


class HashtagEngine:
    """Generates platform-optimized hashtags and SEO keywords."""

    def __init__(self) -> None:
        self._gen_count = 0

    def generate(self, text: str, platform: str = "facebook",
                 categories: Optional[List[str]] = None,
                 custom_hashtags: Optional[List[str]] = None) -> HashtagResult:
        """Generate hashtags and keywords from content."""
        result = HashtagResult(platform=platform)
        max_hashtags = PLATFORM_HASHTAG_LIMITS.get(platform, 5)

        # Extract from text
        auto_tags = self._extract_from_text(text)

        # Category-based
        cat_tags: List[str] = []
        if categories:
            for cat in categories:
                cat_tags.extend(CATEGORY_HASHTAGS.get(cat.lower(), []))

        # Combine and deduplicate
        all_tags = list(dict.fromkeys(auto_tags + cat_tags + (custom_hashtags or [])))
        result.hashtags = all_tags[:max_hashtags]
        result.count = len(result.hashtags)

        # Keywords
        result.keywords = self._extract_keywords(text)
        self._gen_count += 1
        return result

    def generate_seo(self, text: str, focus_keyword: str = "") -> HashtagResult:
        """Generate SEO-focused keywords."""
        result = HashtagResult(platform="seo")
        result.keywords = self._extract_keywords(text)
        if focus_keyword and focus_keyword not in result.keywords:
            result.keywords.insert(0, focus_keyword)
        result.hashtags = []
        self._gen_count += 1
        return result

    def _extract_from_text(self, text: str) -> List[str]:
        words = re.findall(r'\b[A-Z][a-zA-Z]+\b', text)
        return list(dict.fromkeys([f"#{w}" for w in words[:10]]))

    def _extract_keywords(self, text: str) -> List[str]:
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        freq: Dict[str, int] = {}
        for w in words:
            if w not in {"this", "that", "with", "from", "have", "been", "they", "their", "about"}:
                freq[w] = freq.get(w, 0) + 1
        sorted_words = sorted(freq, key=freq.get, reverse=True)
        return sorted_words[:10]

    @property
    def generation_count(self) -> int:
        return self._gen_count
