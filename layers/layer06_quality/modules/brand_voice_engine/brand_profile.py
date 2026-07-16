"""Brand Profile — Data model for brand voice configuration."""
from __future__ import annotations
from typing import Any, Dict, List


class BrandProfile:
    """Complete brand voice profile."""

    __slots__ = (
        "brand_name", "personality", "tone", "formality_level",
        "vocabulary", "forbidden_words", "preferred_words",
        "emoji_style", "emoji_frequency", "preferred_emojis",
        "hashtag_style", "hashtag_count_range", "preferred_hashtags",
        "cta_style", "preferred_ctas",
        "formatting_style", "sentence_length_range",
        "paragraph_length_range", "terminology",
        "target_audience", "industry",
    )

    def __init__(self, brand_name: str = "") -> None:
        self.brand_name = brand_name
        self.personality: List[str] = []  # e.g., ["friendly", "professional", "innovative"]
        self.tone: str = "professional"  # friendly, professional, casual, formal, humorous
        self.formality_level: float = 0.5  # 0=casual, 1=formal
        self.vocabulary: List[str] = []  # brand-specific words
        self.forbidden_words: List[str] = []  # words to never use
        self.preferred_words: List[str] = []  # brand-preferred terms
        self.emoji_style: str = "minimal"  # minimal, moderate, heavy, none
        self.emoji_frequency: float = 0.1  # avg emojis per sentence
        self.preferred_emojis: List[str] = []
        self.hashtag_style: str = "branded"  # branded, minimal, trending, none
        self.hashtag_count_range: tuple = (1, 3)
        self.preferred_hashtags: List[str] = []
        self.cta_style: str = "soft"  # soft, direct, question, none
        self.preferred_ctas: List[str] = []
        self.formatting_style: str = "clean"  # clean, structured, minimal
        self.sentence_length_range: tuple = (10, 25)  # words
        self.paragraph_length_range: tuple = (2, 5)  # sentences
        self.terminology: Dict[str, str] = {}  # term: preferred_form
        self.target_audience: str = ""
        self.industry: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "brand_name": self.brand_name,
            "personality": self.personality,
            "tone": self.tone,
            "formality_level": self.formality_level,
            "vocabulary": self.vocabulary,
            "forbidden_words": self.forbidden_words,
            "preferred_words": self.preferred_words,
            "emoji_style": self.emoji_style,
            "emoji_frequency": self.emoji_frequency,
            "preferred_emojis": self.preferred_emojis,
            "hashtag_style": self.hashtag_style,
            "hashtag_count_range": list(self.hashtag_count_range),
            "preferred_hashtags": self.preferred_hashtags,
            "cta_style": self.cta_style,
            "preferred_ctas": self.preferred_ctas,
            "formatting_style": self.formatting_style,
            "sentence_length_range": list(self.sentence_length_range),
            "paragraph_length_range": list(self.paragraph_length_range),
            "terminology": self.terminology,
            "target_audience": self.target_audience,
            "industry": self.industry,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BrandProfile":
        profile = cls(brand_name=data.get("brand_name", ""))
        profile.personality = data.get("personality", [])
        profile.tone = data.get("tone", "professional")
        profile.formality_level = data.get("formality_level", 0.5)
        profile.vocabulary = data.get("vocabulary", [])
        profile.forbidden_words = data.get("forbidden_words", [])
        profile.preferred_words = data.get("preferred_words", [])
        profile.emoji_style = data.get("emoji_style", "minimal")
        profile.emoji_frequency = data.get("emoji_frequency", 0.1)
        profile.preferred_emojis = data.get("preferred_emojis", [])
        profile.hashtag_style = data.get("hashtag_style", "branded")
        profile.hashtag_count_range = tuple(data.get("hashtag_count_range", [1, 3]))
        profile.preferred_hashtags = data.get("preferred_hashtags", [])
        profile.cta_style = data.get("cta_style", "soft")
        profile.preferred_ctas = data.get("preferred_ctas", [])
        profile.formatting_style = data.get("formatting_style", "clean")
        profile.sentence_length_range = tuple(data.get("sentence_length_range", [10, 25]))
        profile.paragraph_length_range = tuple(data.get("paragraph_length_range", [2, 5]))
        profile.terminology = data.get("terminology", {})
        profile.target_audience = data.get("target_audience", "")
        profile.industry = data.get("industry", "")
        return profile


def create_default_profile(brand_name: str = "default") -> BrandProfile:
    """Create a default brand profile."""
    profile = BrandProfile(brand_name=brand_name)
    profile.personality = ["professional", "informative"]
    profile.tone = "professional"
    profile.formality_level = 0.6
    profile.emoji_style = "minimal"
    profile.hashtag_style = "minimal"
    profile.cta_style = "soft"
    profile.formatting_style = "clean"
    return profile


# Pre-built industry profiles
INDUSTRY_PROFILES: Dict[str, Dict[str, Any]] = {
    "tech": {
        "personality": ["innovative", "forward-thinking", "technical"],
        "tone": "professional",
        "formality_level": 0.5,
        "emoji_style": "minimal",
        "vocabulary": ["innovation", "digital", "platform", "solution", "ecosystem"],
    },
    "finance": {
        "personality": ["trustworthy", "authoritative", "conservative"],
        "tone": "formal",
        "formality_level": 0.8,
        "emoji_style": "none",
        "vocabulary": ["portfolio", "investment", "market", "strategy", "growth"],
    },
    "lifestyle": {
        "personality": ["friendly", "relatable", "inspiring"],
        "tone": "casual",
        "formality_level": 0.3,
        "emoji_style": "moderate",
        "vocabulary": ["wellness", "journey", "inspire", "daily", "tips"],
    },
    "education": {
        "personality": ["knowledgeable", "patient", "encouraging"],
        "tone": "friendly",
        "formality_level": 0.5,
        "emoji_style": "minimal",
        "vocabulary": ["learn", "discover", "understand", "practice", "skill"],
    },
    "healthcare": {
        "personality": ["caring", "professional", "evidence-based"],
        "tone": "professional",
        "formality_level": 0.7,
        "emoji_style": "none",
        "vocabulary": ["health", "wellness", "evidence", "research", "care"],
    },
}
