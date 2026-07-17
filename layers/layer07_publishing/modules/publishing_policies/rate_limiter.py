"""Rate Limiter — Platform-specific API rate limit policies."""
from __future__ import annotations
import time
from typing import Any, Dict


class RateLimitConfig:
    """Rate limit configuration for a platform."""

    __slots__ = ("platform", "requests_per_minute", "requests_per_hour",
                 "posts_per_day", "current_usage", "window_start")

    def __init__(self, platform: str = "") -> None:
        self.platform = platform
        self.requests_per_minute: int = 60
        self.requests_per_hour: int = 200
        self.posts_per_day: int = 25
        self.current_usage: int = 0
        self.window_start: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "requests_per_minute": self.requests_per_minute,
            "requests_per_hour": self.requests_per_hour,
            "posts_per_day": self.posts_per_day,
            "current_usage": self.current_usage,
        }


DEFAULT_RATE_LIMITS: Dict[str, RateLimitConfig] = {
    "facebook": RateLimitConfig("facebook"),
    "instagram": RateLimitConfig("instagram"),
    "twitter": RateLimitConfig("twitter"),
    "linkedin": RateLimitConfig("linkedin"),
    "youtube": RateLimitConfig("youtube"),
    "tiktok": RateLimitConfig("tiktok"),
}


class RateLimiter:
    """Enforce platform-specific rate limits."""

    def __init__(self) -> None:
        self._limits: Dict[str, RateLimitConfig] = {
            k: RateLimitConfig(v.platform) for k, v in DEFAULT_RATE_LIMITS.items()
        }

    def can_publish(self, platform: str) -> bool:
        config = self._limits.get(platform.lower())
        if not config:
            return True
        now = time.time()
        if now - config.window_start >= 3600:
            config.current_usage = 0
            config.window_start = now
        return config.current_usage < config.posts_per_day

    def record_publish(self, platform: str) -> None:
        config = self._limits.get(platform.lower())
        if config:
            config.current_usage += 1

    def get_remaining(self, platform: str) -> int:
        config = self._limits.get(platform.lower())
        if not config:
            return 999
        return max(0, config.posts_per_day - config.current_usage)

    def get_config(self, platform: str) -> RateLimitConfig:
        return self._limits.get(platform.lower(), RateLimitConfig(platform))

    def set_config(self, platform: str, config: RateLimitConfig) -> None:
        self._limits[platform.lower()] = config

    def get_all_configs(self) -> Dict[str, RateLimitConfig]:
        return dict(self._limits)
