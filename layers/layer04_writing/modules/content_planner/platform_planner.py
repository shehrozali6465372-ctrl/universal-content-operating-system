"""Platform Planner — Platform-specific content constraints and recommendations."""
from __future__ import annotations
from threading import RLock
from typing import Any, Dict, List


PLATFORM_SPECS = {
    "facebook": {
        "max_length": 63206,
        "recommended_length": 400,
        "max_hashtags": 5,
        "recommended_hashtags": 3,
        "max_emojis_per_post": 8,
        "content_types": ["post", "story", "reel", "carousel", "live"],
        "best_practices": ["use_questions", "include_cta", "use_images"],
        "algorithm_favors": ["engagement", "shares", "comments"],
    },
    "instagram": {
        "max_length": 2200,
        "recommended_length": 200,
        "max_hashtags": 30,
        "recommended_hashtags": 15,
        "max_emojis_per_post": 12,
        "content_types": ["post", "story", "reel", "carousel"],
        "best_practices": ["use_visual", "use_hashtags", "use_reels"],
        "algorithm_favors": ["saves", "shares", "reels"],
    },
    "twitter": {
        "max_length": 280,
        "recommended_length": 200,
        "max_hashtags": 3,
        "recommended_hashtags": 2,
        "max_emojis_per_post": 4,
        "content_types": ["tweet", "thread"],
        "best_practices": ["use_threads", "use_images", "engage_replies"],
        "algorithm_favors": ["retweets", "replies", "likes"],
    },
    "linkedin": {
        "max_length": 3000,
        "recommended_length": 800,
        "max_hashtags": 5,
        "recommended_hashtags": 3,
        "max_emojis_per_post": 4,
        "content_types": ["post", "article", "newsletter"],
        "best_practices": ["use_professional_tone", "share_insights", "use_data"],
        "algorithm_favors": ["comments", "reposts", "dwell_time"],
    },
    "tiktok": {
        "max_length": 2200, "recommended_length": 200, "max_hashtags": 8,
        "recommended_hashtags": 5, "max_emojis_per_post": 8,
        "content_types": ["video", "short"],
        "best_practices": ["use_hook", "use_trends", "use_visual"],
        "algorithm_favors": ["watch_time", "completion_rate", "shares"],
    },
    "youtube": {
        "max_length": 5000,
        "recommended_length": 1000,
        "max_hashtags": 15,
        "recommended_hashtags": 5,
        "max_emojis_per_post": 6,
        "content_types": ["video", "short", "community_post"],
        "best_practices": ["use_thumbnail", "strong_hook", "end_screen"],
        "algorithm_favors": ["watch_time", "ctr", "engagement"],
    },
}


class PlatformConstraints:
    """Platform-specific constraints for content."""
    __slots__ = ("platform", "max_length", "recommended_length",
                 "max_hashtags", "recommended_hashtags", "max_emojis",
                 "content_types", "best_practices", "algorithm_favors")

    def __init__(self, platform: str = "facebook") -> None:
        if platform not in PLATFORM_SPECS:
            raise ValueError(f"Unsupported platform: {platform}")
        self.platform = platform
        spec = PLATFORM_SPECS[platform]
        self.max_length = spec["max_length"]
        self.recommended_length = spec["recommended_length"]
        self.max_hashtags = spec["max_hashtags"]
        self.recommended_hashtags = spec["recommended_hashtags"]
        self.max_emojis = spec["max_emojis_per_post"]
        self.content_types = list(spec["content_types"])
        self.best_practices = list(spec["best_practices"])
        self.algorithm_favors = list(spec["algorithm_favors"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "max_length": self.max_length,
            "recommended_length": self.recommended_length,
            "max_hashtags": self.max_hashtags,
            "recommended_hashtags": self.recommended_hashtags,
            "max_emojis": self.max_emojis,
            "content_types": list(self.content_types),
            "best_practices": list(self.best_practices),
            "algorithm_favors": list(self.algorithm_favors),
        }


class PlatformPlanner:
    """Provides platform-specific constraints and recommendations."""

    def __init__(self) -> None:
        self._constraints_cache: Dict[str, PlatformConstraints] = {}
        self._lock = RLock()

    def get_constraints(self, platform: str) -> PlatformConstraints:
        """Get constraints for a platform."""
        with self._lock:
            if platform not in self._constraints_cache:
                self._constraints_cache[platform] = PlatformConstraints(platform)
            cached = self._constraints_cache[platform]
            copy = PlatformConstraints(platform)
            copy.max_length = cached.max_length
            copy.recommended_length = cached.recommended_length
            copy.max_hashtags = cached.max_hashtags
            copy.recommended_hashtags = cached.recommended_hashtags
            copy.max_emojis = cached.max_emojis
            copy.content_types = list(cached.content_types)
            copy.best_practices = list(cached.best_practices)
            copy.algorithm_favors = list(cached.algorithm_favors)
            return copy

    def recommend(self, platform: str, goal: str = "educate") -> Dict[str, Any]:
        """Recommend content parameters for a platform and goal."""
        constraints = self.get_constraints(platform)
        recommendations: Dict[str, Any] = {
            "platform": platform,
            "length": "medium",
            "content_type": constraints.content_types[0] if constraints.content_types else "post",
            "hashtag_count": constraints.recommended_hashtags,
            "emoji_level": "medium",
            "best_practices": [],
        }

        if goal == "educate":
            recommendations["content_type"] = "post" if "post" in constraints.content_types else constraints.content_types[0]
            recommendations["best_practices"] = [p for p in constraints.best_practices if "question" in p or "cta" in p or "image" in p]
        elif goal == "entertain":
            recommendations["content_type"] = "reel" if "reel" in constraints.content_types else constraints.content_types[0]
            recommendations["emoji_level"] = "high"
        elif goal == "promote":
            recommendations["content_type"] = "post"
            recommendations["best_practices"] = constraints.best_practices[:2]

        return recommendations

    def validate_length(self, platform: str, text_length: int) -> Dict[str, Any]:
        """Validate text length against platform constraints."""
        c = self.get_constraints(platform)
        return {
            "valid": text_length <= c.max_length,
            "length": text_length,
            "max": c.max_length,
            "recommended": c.recommended_length,
            "ratio": round(text_length / c.max_length, 3),
        }

    @property
    def supported_platforms(self) -> List[str]:
        return list(PLATFORM_SPECS.keys())
