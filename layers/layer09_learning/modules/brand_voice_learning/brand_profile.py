"""Brand Profile — Data model for brand voice identity."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List

_BP_COUNTER = itertools.count(1)

BRAND_INDUSTRIES = (
    "technology", "finance", "healthcare", "education", "lifestyle",
    "entertainment", "ecommerce", "media", "saas", "general",
)
BRAND_STATUSES = ("draft", "active", "learning", "mature", "archived")


class BrandProfile:
    """Complete brand voice identity profile."""

    __slots__ = (
        "profile_id", "version", "status", "name", "industry",
        "personality_traits", "tone_profile", "formality_level",
        "vocabulary_preferences", "forbidden_words", "preferred_words",
        "terminology", "sentence_style", "paragraph_style",
        "emoji_style", "cta_style", "hashtag_style",
        "target_audience", "supported_platforms",
        "created_at", "updated_at",
        "usage_count", "consistency_score",
        "tags", "metadata", "parent_id",
    )

    def __init__(self, name: str = "", industry: str = "general") -> None:
        self.profile_id: str = f"brp_{next(_BP_COUNTER)}"
        self.version: int = 1
        self.status: str = "draft"
        self.name: str = name
        self.industry: str = industry if industry in BRAND_INDUSTRIES else "general"
        self.personality_traits: List[str] = []
        self.tone_profile: Dict[str, float] = {}
        self.formality_level: str = "medium"
        self.vocabulary_preferences: Dict[str, float] = {}
        self.forbidden_words: List[str] = []
        self.preferred_words: List[str] = []
        self.terminology: Dict[str, str] = {}
        self.sentence_style: str = "varied"
        self.paragraph_style: str = "short"
        self.emoji_style: str = "moderate"
        self.cta_style: str = "engagement"
        self.hashtag_style: str = "moderate"
        self.target_audience: str = ""
        self.supported_platforms: List[str] = []
        self.created_at: float = time.time()
        self.updated_at: float = time.time()
        self.usage_count: int = 0
        self.consistency_score: float = 0.0
        self.tags: List[str] = []
        self.metadata: Dict[str, Any] = {}
        self.parent_id: str = ""

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def tone_count(self) -> int:
        return len(self.tone_profile)

    @property
    def vocabulary_size(self) -> int:
        return len(self.vocabulary_preferences)

    def add_tone(self, tone: str, weight: float = 0.5) -> None:
        self.tone_profile[tone] = round(max(0.0, min(1.0, weight)), 3)
        self.updated_at = time.time()

    def add_vocabulary(self, word: str, frequency: float = 0.5) -> None:
        self.vocabulary_preferences[word] = round(max(0.0, min(1.0, frequency)), 3)
        self.updated_at = time.time()

    def add_forbidden_word(self, word: str) -> None:
        if word not in self.forbidden_words:
            self.forbidden_words.append(word)
            self.updated_at = time.time()

    def add_preferred_word(self, word: str) -> None:
        if word not in self.preferred_words:
            self.preferred_words.append(word)
            self.updated_at = time.time()

    def add_terminology(self, term: str, definition: str = "") -> None:
        self.terminology[term] = definition
        self.updated_at = time.time()

    def record_usage(self, consistency: float = 0.0) -> None:
        self.usage_count += 1
        n = self.usage_count
        self.consistency_score = round(
            ((self.consistency_score * (n - 1)) + consistency) / n, 4,
        )
        self.updated_at = time.time()

    def fork(self) -> "BrandProfile":
        child = BrandProfile(name=self.name, industry=self.industry)
        child.version = self.version + 1
        child.parent_id = self.profile_id
        child.personality_traits = list(self.personality_traits)
        child.tone_profile = dict(self.tone_profile)
        child.formality_level = self.formality_level
        child.vocabulary_preferences = dict(self.vocabulary_preferences)
        child.forbidden_words = list(self.forbidden_words)
        child.preferred_words = list(self.preferred_words)
        child.terminology = dict(self.terminology)
        child.sentence_style = self.sentence_style
        child.paragraph_style = self.paragraph_style
        child.emoji_style = self.emoji_style
        child.cta_style = self.cta_style
        child.hashtag_style = self.hashtag_style
        child.target_audience = self.target_audience
        child.supported_platforms = list(self.supported_platforms)
        child.tags = list(self.tags)
        return child

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "version": self.version,
            "status": self.status,
            "name": self.name,
            "industry": self.industry,
            "personality_traits": self.personality_traits,
            "tone_profile": self.tone_profile,
            "formality_level": self.formality_level,
            "vocabulary_size": self.vocabulary_size,
            "forbidden_words": self.forbidden_words,
            "preferred_words": self.preferred_words,
            "consistency_score": self.consistency_score,
            "usage_count": self.usage_count,
            "tags": self.tags,
        }
