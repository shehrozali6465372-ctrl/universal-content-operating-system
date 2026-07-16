"""Image Memory — Brand visual consistency across platforms."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class BrandVisualProfile:
    """Visual brand profile."""
    __slots__ = ("name", "primary_colors", "secondary_colors", "fonts",
                 "style", "mood", "donts", "platform_profiles")

    def __init__(self, name: str = "") -> None:
        self.name = name
        self.primary_colors: List[str] = []
        self.secondary_colors: List[str] = []
        self.fonts: List[str] = []
        self.style = "modern"
        self.mood = "professional"
        self.donts: List[str] = []
        self.platform_profiles: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "primary_colors": self.primary_colors,
            "style": self.style,
            "mood": self.mood,
        }


class ImageMemory:
    """Stores visual brand profiles and image history."""

    def __init__(self) -> None:
        self._profiles: Dict[str, BrandVisualProfile] = {}
        self._history: List[Dict[str, Any]] = []

    def set_profile(self, name: str, colors: Optional[List[str]] = None,
                    style: str = "modern", mood: str = "professional") -> BrandVisualProfile:
        p = BrandVisualProfile(name=name)
        p.primary_colors = colors or []
        p.style = style
        p.mood = mood
        self._profiles[name] = p
        return p

    def get_profile(self, name: str) -> Optional[BrandVisualProfile]:
        return self._profiles.get(name)

    def store_image(self, platform: str, topic: str, url: str,
                    profile_name: str = "") -> Dict[str, Any]:
        record = {"platform": platform, "topic": topic, "url": url,
                  "profile": profile_name, "timestamp": time.time()}
        self._history.append(record)
        return record

    def get_history(self, platform: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        if platform:
            return [r for r in self._history if r["platform"] == platform][-limit:]
        return self._history[-limit:]

    @property
    def profile_count(self) -> int:
        return len(self._profiles)

    @property
    def history_count(self) -> int:
        return len(self._history)
