"""Image Memory — Brand visual consistency across platforms."""
from __future__ import annotations
import time
from threading import RLock
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
            "primary_colors": list(self.primary_colors),
            "style": self.style,
            "mood": self.mood,
        }


class ImageMemory:
    """Stores visual brand profiles and bounded image history."""

    MAX_HISTORY = 1000

    def __init__(self) -> None:
        self._profiles: Dict[str, BrandVisualProfile] = {}
        self._history: List[Dict[str, Any]] = []
        self._lock = RLock()

    def set_profile(self, name: str, colors: Optional[List[str]] = None,
                    style: str = "modern", mood: str = "professional") -> BrandVisualProfile:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("profile name must not be empty")
        if colors is not None and not isinstance(colors, list):
            raise ValueError("colors must be a list")
        p = BrandVisualProfile(name=name.strip())
        p.primary_colors = list(colors or [])
        p.style = style
        p.mood = mood
        with self._lock:
            self._profiles[p.name] = p
        return p

    def get_profile(self, name: str) -> Optional[BrandVisualProfile]:
        with self._lock:
            profile = self._profiles.get(name)
            if profile is None:
                return None
            snapshot = BrandVisualProfile(profile.name)
            snapshot.primary_colors = list(profile.primary_colors)
            snapshot.secondary_colors = list(profile.secondary_colors)
            snapshot.fonts = list(profile.fonts)
            snapshot.style = profile.style
            snapshot.mood = profile.mood
            snapshot.donts = list(profile.donts)
            snapshot.platform_profiles = dict(profile.platform_profiles)
            return snapshot

    def store_image(self, platform: str, topic: str, url: str,
                    profile_name: str = "") -> Dict[str, Any]:
        if not isinstance(platform, str) or not platform.strip():
            raise ValueError("platform must not be empty")
        if not isinstance(topic, str) or not topic.strip():
            raise ValueError("topic must not be empty")
        if not isinstance(url, str) or not url.strip():
            raise ValueError("url must not be empty")
        with self._lock:
            if profile_name and profile_name not in self._profiles:
                raise ValueError("Unknown visual profile: " + profile_name)
            record = {
                "platform": platform.strip(),
                "topic": topic.strip(),
                "url": url.strip(),
                "profile": profile_name,
                "timestamp": time.time(),
            }
            self._history.append(record)
            if len(self._history) > self.MAX_HISTORY:
                del self._history[:-self.MAX_HISTORY]
            return dict(record)

    def get_history(self, platform: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1 or limit > self.MAX_HISTORY:
            raise ValueError(f"limit must be between 1 and {self.MAX_HISTORY}")
        with self._lock:
            if platform:
                records = [r for r in self._history if r["platform"] == platform][-limit:]
            else:
                records = self._history[-limit:]
            return [dict(record) for record in records]

    @property
    def profile_count(self) -> int:
        with self._lock:
            return len(self._profiles)

    @property
    def history_count(self) -> int:
        with self._lock:
            return len(self._history)
