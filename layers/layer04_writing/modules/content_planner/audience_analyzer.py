"""Audience Analyzer — Determine audience characteristics for content planning."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


AUDIENCE_PROFILES = {
    "students": {"tone": "friendly", "length": "medium", "emoji_level": "high",
                 "language_preference": "casual", "content偏好": "educational"},
    "professionals": {"tone": "professional", "length": "long", "emoji_level": "low",
                      "language_preference": "formal", "content_preference": "informative"},
    "general": {"tone": "friendly", "length": "medium", "emoji_level": "medium",
                "language_preference": "mixed", "content_preference": "mixed"},
    "entrepreneurs": {"tone": "enthusiastic", "length": "medium", "emoji_level": "medium",
                      "language_preference": "motivational", "content_preference": "educational"},
    "tech_enthusiasts": {"tone": "informative", "length": "long", "emoji_level": "low",
                         "language_preference": "technical", "content_preference": "detailed"},
    "parents": {"tone": "warm", "length": "medium", "emoji_level": "medium",
                "language_preference": "friendly", "content_preference": "practical"},
    "creators": {"tone": "casual", "length": "short", "emoji_level": "high",
                 "language_preference": "trendy", "content_preference": "inspiring"},
}


class AudienceAnalysis:
    """Result of audience analysis."""
    __slots__ = ("audience_type", "confidence", "recommended_tone",
                 "recommended_length", "recommended_emoji_level",
                 "language_style", "content_preference", "reasons")

    def __init__(self) -> None:
        self.audience_type = "general"
        self.confidence = 0.5
        self.recommended_tone = "friendly"
        self.recommended_length = "medium"
        self.recommended_emoji_level = "medium"
        self.language_style = "mixed"
        self.content_preference = "mixed"
        self.reasons: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audience_type": self.audience_type,
            "confidence": round(self.confidence, 3),
            "recommended_tone": self.recommended_tone,
            "recommended_length": self.recommended_length,
            "recommended_emoji_level": self.recommended_emoji_level,
            "language_style": self.language_style,
            "content_preference": self.content_preference,
            "reasons": self.reasons,
        }


class AudienceAnalyzer:
    """Analyzes audience data to recommend content parameters."""

    def __init__(self) -> None:
        self._analysis_count = 0

    def analyze(
        self,
        topic: str,
        audience_hint: Optional[str] = None,
        intel_data: Optional[Dict[str, Any]] = None,
    ) -> AudienceAnalysis:
        """Analyze audience and recommend content parameters."""
        result = AudienceAnalysis()

        if audience_hint and audience_hint.lower() in AUDIENCE_PROFILES:
            result.audience_type = audience_hint.lower()
            result.confidence = 0.85
            result.reasons.append(f"Explicit audience specified: {audience_hint}")
        else:
            detected = self._detect_audience(topic, intel_data or {})
            result.audience_type = detected["type"]
            result.confidence = detected["confidence"]
            result.reasons = detected["reasons"]

        # Apply profile
        profile = AUDIENCE_PROFILES.get(result.audience_type, AUDIENCE_PROFILES["general"])
        result.recommended_tone = profile["tone"]
        result.recommended_length = profile["length"]
        result.recommended_emoji_level = profile["emoji_level"]
        result.language_style = profile["language_preference"]
        result.content_preference = profile.get("content_preference", "mixed")

        self._analysis_count += 1
        return result

    def _detect_audience(self, topic: str, intel: Dict[str, Any]) -> Dict[str, Any]:
        topic_lower = topic.lower()
        scores: Dict[str, float] = {}

        audience_signals = {
            "students": ["learn", "tutorial", "beginner", "course", "study"],
            "professionals": ["career", "business", "enterprise", "strategy", "management"],
            "tech_enthusiasts": ["code", "api", "algorithm", "framework", "python"],
            "entrepreneurs": ["startup", "revenue", "growth", "hustle", "business"],
            "parents": ["family", "kids", "health", "safety", "education"],
            "creators": ["content", "design", "creative", "art", "video"],
        }

        for aud, keywords in audience_signals.items():
            score = sum(0.15 for kw in keywords if kw in topic_lower)
            scores[aud] = score

        # Check intel engagement data
        engagement = intel.get("expected_engagement", 0)
        if engagement > 0.7:
            scores["general"] = scores.get("general", 0) + 0.2

        best = max(scores, key=scores.get) if scores else "general"
        confidence = min(scores.get(best, 0) + 0.3, 1.0)

        return {
            "type": best if scores.get(best, 0) > 0 else "general",
            "confidence": confidence,
            "reasons": [f"Topic analysis suggests '{best}' audience"],
        }

    @property
    def analysis_count(self) -> int:
        return self._analysis_count
