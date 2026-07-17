"""PlatformAdapter — Adapt content to platform requirements."""
from __future__ import annotations
from typing import Any, Dict, List


class PlatformAdapter:
    """Adapt generated content to meet platform-specific requirements."""

    PLATFORM_RULES = {
        "facebook": {"tone": "friendly", "emoji_preferred": True, "link_preview": True},
        "instagram": {"tone": "casual", "emoji_preferred": True, "hashtag_heavy": True},
        "x": {"tone": "direct", "emoji_preferred": False, "concise": True},
        "linkedin": {"tone": "professional", "emoji_preferred": False, "long_form": True},
        "youtube": {"tone": "engaging", "emoji_preferred": True, "description_heavy": True},
        "tiktok": {"tone": "energetic", "emoji_preferred": True, "short_form": True},
        "pinterest": {"tone": "inspirational", "emoji_preferred": True, "visual_heavy": True},
        "threads": {"tone": "conversational", "emoji_preferred": False, "concise": True},
        "medium": {"tone": "thoughtful", "emoji_preferred": False, "long_form": True},
        "wordpress": {"tone": "informative", "emoji_preferred": False, "long_form": True},
        "reddit": {"tone": "authentic", "emoji_preferred": False, "detailed": True},
        "telegram": {"tone": "informative", "emoji_preferred": True, "concise": True},
        "discord": {"tone": "casual", "emoji_preferred": True, "concise": True},
        "binance_square": {"tone": "analytical", "emoji_preferred": False, "technical": True},
    }

    def __init__(self) -> None:
        self._custom_rules: Dict[str, Dict[str, Any]] = {}

    def adapt(self, text: str, platform: str) -> str:
        rules = self._custom_rules.get(platform, self.PLATFORM_RULES.get(platform, {}))
        adapted = text
        if rules.get("concise") and len(adapted) > 280:
            adapted = adapted[:277] + "..."
        if not rules.get("emoji_preferred"):
            adapted = "".join(c for c in adapted if ord(c) <= 0x1F600 or ord(c) > 0x1F900)
        return adapted

    def get_rules(self, platform: str) -> Dict[str, Any]:
        return self._custom_rules.get(platform, self.PLATFORM_RULES.get(platform, {}))

    def set_rules(self, platform: str, rules: Dict[str, Any]) -> None:
        self._custom_rules[platform] = rules

    def get_supported_platforms(self) -> List[str]:
        return list(set(list(self.PLATFORM_RULES.keys()) + list(self._custom_rules.keys())))
