"""ToneEngine — Manage content tone and style."""
from __future__ import annotations
from typing import Any, Dict, List


TONE_PROFILES = {
    "professional": {"formality": 0.9, "humor": 0.1, "enthusiasm": 0.3, "authority": 0.8},
    "casual": {"formality": 0.3, "humor": 0.5, "enthusiasm": 0.7, "authority": 0.3},
    "educational": {"formality": 0.7, "humor": 0.2, "enthusiasm": 0.5, "authority": 0.7},
    "inspirational": {"formality": 0.5, "humor": 0.3, "enthusiasm": 0.8, "authority": 0.5},
    "authoritative": {"formality": 0.8, "humor": 0.1, "enthusiasm": 0.4, "authority": 0.9},
    "friendly": {"formality": 0.4, "humor": 0.4, "enthusiasm": 0.7, "authority": 0.3},
    "humorous": {"formality": 0.2, "humor": 0.9, "enthusiasm": 0.6, "authority": 0.2},
    "urgent": {"formality": 0.6, "humor": 0.0, "enthusiasm": 0.9, "authority": 0.7},
}


class ToneProfile:
    """A tone configuration profile."""

    __slots__ = ("name", "formality", "humor", "enthusiasm", "authority")

    def __init__(self, name: str = "professional") -> None:
        self.name = name
        profile = TONE_PROFILES.get(name, TONE_PROFILES["professional"])
        self.formality = profile["formality"]
        self.humor = profile["humor"]
        self.enthusiasm = profile["enthusiasm"]
        self.authority = profile["authority"]

    def to_dict(self) -> Dict[str, float]:
        return {"formality": self.formality, "humor": self.humor,
                "enthusiasm": self.enthusiasm, "authority": self.authority}


class ToneEngine:
    """Manage and apply content tone."""

    def __init__(self) -> None:
        self._active_tone: ToneProfile = ToneProfile("professional")
        self._tone_history: List[Dict[str, Any]] = []

    def set_tone(self, tone_name: str) -> ToneProfile:
        self._active_tone = ToneProfile(tone_name)
        self._tone_history.append({"tone": tone_name, "profile": self._active_tone.to_dict()})
        return self._active_tone

    def get_tone(self) -> ToneProfile:
        return self._active_tone

    def blend_tones(self, tone1: str, tone2: str, ratio: float = 0.5) -> ToneProfile:
        p1 = ToneProfile(tone1)
        p2 = ToneProfile(tone2)
        blended = ToneProfile("blended")
        blended.formality = round(p1.formality * (1 - ratio) + p2.formality * ratio, 3)
        blended.humor = round(p1.humor * (1 - ratio) + p2.humor * ratio, 3)
        blended.enthusiasm = round(p1.enthusiasm * (1 - ratio) + p2.enthusiasm * ratio, 3)
        blended.authority = round(p1.authority * (1 - ratio) + p2.authority * ratio, 3)
        return blended

    def get_available_tones(self) -> List[str]:
        return list(TONE_PROFILES.keys())

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._tone_history[-limit:]
