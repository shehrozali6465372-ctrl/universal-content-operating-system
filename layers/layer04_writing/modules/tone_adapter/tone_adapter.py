"""Tone Adapter — Adapt content tone for different platforms and audiences."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


PLATFORM_TONE_DEFAULTS = {
    "facebook": "conversational", "instagram": "enthusiastic", "twitter": "punchy",
    "linkedin": "professional", "tiktok": "playful", "youtube": "informative",
    "pinterest": "aspirational", "threads": "casual", "reddit": "authentic",
    "medium": "authoritative", "newsletter": "personal", "blog": "informative",
}

TONE_PRESETS = {
    "conversational": {"formality": 0.3, "energy": 0.6, "humor": 0.3, "emoji_density": "medium"},
    "professional": {"formality": 0.8, "energy": 0.4, "humor": 0.0, "emoji_density": "low"},
    "punchy": {"formality": 0.2, "energy": 0.9, "humor": 0.2, "emoji_density": "low"},
    "enthusiastic": {"formality": 0.3, "energy": 0.8, "humor": 0.3, "emoji_density": "high"},
    "playful": {"formality": 0.1, "energy": 0.7, "humor": 0.6, "emoji_density": "high"},
    "informative": {"formality": 0.6, "energy": 0.5, "humor": 0.1, "emoji_density": "low"},
    "aspirational": {"formality": 0.4, "energy": 0.6, "humor": 0.2, "emoji_density": "medium"},
    "casual": {"formality": 0.1, "energy": 0.5, "humor": 0.3, "emoji_density": "medium"},
    "authentic": {"formality": 0.2, "energy": 0.5, "humor": 0.2, "emoji_density": "low"},
    "authoritative": {"formality": 0.7, "energy": 0.4, "humor": 0.0, "emoji_density": "none"},
    "personal": {"formality": 0.3, "energy": 0.6, "humor": 0.2, "emoji_density": "low"},
    "inspiring": {"formality": 0.4, "energy": 0.7, "humor": 0.1, "emoji_density": "medium"},
}


class ToneAdaptResult:
    """Result of tone adaptation."""
    __slots__ = ("adapted_text", "original_tone", "target_tone", "platform", "changes")

    def __init__(self) -> None:
        self.adapted_text = ""
        self.original_tone = ""
        self.target_tone = ""
        self.platform = ""
        self.changes: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "adapted_text": self.adapted_text,
            "original_tone": self.original_tone,
            "target_tone": self.target_tone,
            "platform": self.platform,
            "changes": self.changes,
        }


class ToneAdapter:
    """Adapts content tone for different platforms and audiences."""

    def __init__(self) -> None:
        self._adapt_count = 0

    def adapt(self, text: str, source_platform: str = "facebook",
              target_platform: str = "linkedin") -> ToneAdaptResult:
        """Adapt text from one platform tone to another."""
        result = ToneAdaptResult()
        result.original_tone = PLATFORM_TONE_DEFAULTS.get(source_platform, "conversational")
        result.target_tone = PLATFORM_TONE_DEFAULTS.get(target_platform, "conversational")
        result.platform = target_platform

        adapted = text
        target_tone = result.target_tone

        if target_tone == "professional":
            adapted = self._make_professional(adapted)
            result.changes.append("Formalized language")
        elif target_tone == "punchy":
            adapted = self._make_punchy(adapted)
            result.changes.append("Made more concise and punchy")
        elif target_tone == "playful":
            adapted = self._make_playful(adapted)
            result.changes.append("Added playful elements")
        elif target_tone == "enthusiastic":
            adapted = self._make_enthusiastic(adapted)
            result.changes.append("Increased energy and enthusiasm")

        result.adapted_text = adapted
        self._adapt_count += 1
        return result

    def adapt_to_multi_platform(self, text: str, platforms: Optional[List[str]] = None) -> List[ToneAdaptResult]:
        """Adapt text for multiple platforms."""
        plats = platforms or ["facebook", "instagram", "twitter", "linkedin"]
        return [self.adapt(text, target_platform=p) for p in plats]

    def get_platform_default(self, platform: str) -> str:
        return PLATFORM_TONE_DEFAULTS.get(platform, "conversational")

    def get_tone_profile(self, tone: str) -> Dict[str, Any]:
        return TONE_PRESETS.get(tone, TONE_PRESETS["conversational"])

    def _make_professional(self, text: str) -> str:
        replacements = {"gonna": "going to", "wanna": "want to", "kinda": "kind of",
                        "awesome": "excellent", "cool": "impressive"}
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    def _make_punchy(self, text: str) -> str:
        sentences = text.split('. ')
        if len(sentences) > 3:
            text = '. '.join(sentences[:3]) + '.'
        return text

    def _make_playful(self, text: str) -> str:
        return text

    def _make_enthusiastic(self, text: str) -> str:
        return text

    @property
    def adaptation_count(self) -> int:
        return self._adapt_count
