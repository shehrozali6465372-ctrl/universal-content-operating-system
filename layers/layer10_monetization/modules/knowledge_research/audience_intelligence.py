"""AudienceIntelligence — Learn audience preferences and behavior."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_AI_COUNTER = itertools.count(1)


class AudienceProfile:
    """Audience intelligence profile."""

    __slots__ = ("profile_id", "platform", "interests", "active_hours",
                 "languages", "devices", "locations", "age_groups",
                 "behaviors", "content_preferences", "updated_at")

    def __init__(self, platform: str = "") -> None:
        self.profile_id: str = f"aud_{next(_AI_COUNTER)}"
        self.platform = platform
        self.interests: List[str] = []
        self.active_hours: List[int] = []
        self.languages: List[str] = []
        self.devices: Dict[str, float] = {}
        self.locations: Dict[str, float] = {}
        self.age_groups: Dict[str, float] = {}
        self.behaviors: List[str] = []
        self.content_preferences: List[str] = []
        self.updated_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"profile_id": self.profile_id, "platform": self.platform,
                "interests": self.interests, "languages": self.languages}


class AudienceIntelligence:
    """Learn and track audience preferences across platforms."""

    def __init__(self) -> None:
        self._profiles: List[AudienceProfile] = []
        self._insights: List[Dict[str, Any]] = []

    def create_profile(self, platform: str) -> AudienceProfile:
        profile = AudienceProfile(platform)
        self._profiles.append(profile)
        return profile

    def update_profile(self, profile_id: str, data: Dict[str, Any]) -> Optional[AudienceProfile]:
        for p in self._profiles:
            if p.profile_id == profile_id:
                for k, v in data.items():
                    if hasattr(p, k):
                        setattr(p, k, v)
                p.updated_at = time.time()
                return p
        return None

    def get_profile(self, platform: str) -> Optional[AudienceProfile]:
        for p in self._profiles:
            if p.platform == platform:
                return p
        return None

    def get_all_profiles(self) -> List[AudienceProfile]:
        return list(self._profiles)

    def get_insights(self, platform: str = "") -> List[Dict[str, Any]]:
        results = self._insights
        if platform:
            results = [i for i in results if i.get("platform") == platform]
        return results

    def get_stats(self) -> Dict[str, Any]:
        return {"total_profiles": len(self._profiles),
                "total_insights": len(self._insights)}
