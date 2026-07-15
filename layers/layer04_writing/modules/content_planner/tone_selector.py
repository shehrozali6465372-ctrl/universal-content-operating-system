"""Tone Selector — Select appropriate writing tone based on context."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


TONE_PROFILES = {
    "friendly": {"formality": 0.3, "emotion": 0.6, "humor": 0.3, "vocabulary": "simple"},
    "professional": {"formality": 0.8, "emotion": 0.2, "humor": 0.0, "vocabulary": "formal"},
    "casual": {"formality": 0.1, "emotion": 0.5, "humor": 0.4, "vocabulary": "simple"},
    "informative": {"formality": 0.6, "emotion": 0.2, "humor": 0.1, "vocabulary": "technical"},
    "humorous": {"formality": 0.1, "emotion": 0.7, "humor": 0.9, "vocabulary": "casual"},
    "inspiring": {"formality": 0.4, "emotion": 0.8, "humor": 0.1, "vocabulary": "eloquent"},
    "enthusiastic": {"formality": 0.2, "emotion": 0.8, "humor": 0.3, "vocabulary": "energetic"},
    "warm": {"formality": 0.3, "emotion": 0.7, "humor": 0.2, "vocabulary": "simple"},
    "conversational": {"formality": 0.2, "emotion": 0.5, "humor": 0.3, "vocabulary": "casual"},
    "playful": {"formality": 0.1, "emotion": 0.6, "humor": 0.7, "vocabulary": "fun"},
}


class ToneSelection:
    """Result of tone selection."""
    __slots__ = ("selected_tone", "confidence", "profile", "alternatives", "reasons")

    def __init__(self) -> None:
        self.selected_tone = "friendly"
        self.confidence = 0.5
        self.profile: Dict[str, Any] = {}
        self.alternatives: List[str] = []
        self.reasons: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_tone": self.selected_tone,
            "confidence": round(self.confidence, 3),
            "profile": self.profile,
            "alternatives": self.alternatives,
            "reasons": self.reasons,
        }


class ToneSelector:
    """Selects writing tone based on goal, audience, and platform."""

    GOAL_TONE_MAP = {
        "educate": ["friendly", "informative", "professional"],
        "entertain": ["humorous", "casual", "playful"],
        "inspire": ["inspiring", "warm", "enthusiastic"],
        "promote": ["enthusiastic", "professional", "friendly"],
        "engage": ["conversational", "casual", "playful"],
    }

    def __init__(self) -> None:
        self._selection_history: List[ToneSelection] = []

    def select(
        self,
        goal: str = "educate",
        audience: str = "general",
        platform: str = "facebook",
        override: Optional[str] = None,
    ) -> ToneSelection:
        """Select the best tone for given context."""
        result = ToneSelection()

        if override and override in TONE_PROFILES:
            result.selected_tone = override
            result.confidence = 0.95
            result.reasons.append(f"Explicit tone override: {override}")
            result.profile = TONE_PROFILES[override]
            result.alternatives = [t for t in self.GOAL_TONE_MAP.get(goal, ["friendly"]) if t != override]
            self._selection_history.append(result)
            return result

        # Get candidates from goal
        candidates = self.GOAL_TONE_MAP.get(goal, ["friendly"])

        # Adjust by audience
        if audience == "professionals" and "professional" in candidates:
            result.selected_tone = "professional"
            result.confidence = 0.85
            result.reasons.append("Professional audience detected")
        elif audience == "students" and "friendly" in candidates:
            result.selected_tone = "friendly"
            result.confidence = 0.8
            result.reasons.append("Student audience — friendly tone preferred")
        else:
            result.selected_tone = candidates[0] if candidates else "friendly"
            result.confidence = 0.6
            result.reasons.append(f"Default tone for goal '{goal}'")

        result.profile = TONE_PROFILES.get(result.selected_tone, TONE_PROFILES["friendly"])
        result.alternatives = [c for c in candidates if c != result.selected_tone]

        self._selection_history.append(result)
        return result

    def get_profile(self, tone: str) -> Dict[str, Any]:
        """Get the profile for a specific tone."""
        return TONE_PROFILES.get(tone, TONE_PROFILES["friendly"])

    @property
    def available_tones(self) -> List[str]:
        return list(TONE_PROFILES.keys())
