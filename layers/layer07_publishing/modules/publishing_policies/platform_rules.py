"""Platform Rules — Centralized rules for each platform."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class PlatformRule:
    """A single publishing rule for a platform."""

    __slots__ = ("rule_id", "platform", "rule_type", "description",
                 "config", "version", "enabled")

    def __init__(
        self,
        rule_id: str = "",
        platform: str = "",
        rule_type: str = "",
        description: str = "",
    ) -> None:
        self.rule_id = rule_id
        self.platform = platform
        self.rule_type = rule_type
        self.description = description
        self.config: Dict[str, Any] = {}
        self.version: str = "1.0.0"
        self.enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "platform": self.platform,
            "rule_type": self.rule_type,
            "description": self.description,
            "config": self.config,
            "version": self.version,
            "enabled": self.enabled,
        }


class PlatformRules:
    """Centralized rules database for all platforms."""

    def __init__(self) -> None:
        self._rules: Dict[str, List[PlatformRule]] = {}
        self._initialize_default_rules()

    def _initialize_default_rules(self) -> None:
        """Initialize default rules for common platforms."""
        defaults = {
            "facebook": [
                PlatformRule("fb_text", "facebook", "content_length", "Max text length"),
                PlatformRule("fb_images", "facebook", "media", "Image posting rules"),
                PlatformRule("fb_link", "facebook", "link", "Link sharing rules"),
            ],
            "instagram": [
                PlatformRule("ig_text", "instagram", "content_length", "Caption length"),
                PlatformRule("ig_images", "instagram", "media", "Image posting rules"),
                PlatformRule("ig_hashtags", "instagram", "hashtag", "Hashtag rules"),
            ],
            "twitter": [
                PlatformRule("tw_text", "twitter", "content_length", "Tweet length"),
                PlatformRule("tw_media", "twitter", "media", "Media posting rules"),
            ],
            "linkedin": [
                PlatformRule("li_text", "linkedin", "content_length", "Post length"),
                PlatformRule("li_articles", "linkedin", "article", "Article rules"),
            ],
            "youtube": [
                PlatformRule("yt_video", "youtube", "video", "Video upload rules"),
                PlatformRule("yt_desc", "youtube", "description", "Description rules"),
            ],
            "tiktok": [
                PlatformRule("tt_video", "tiktok", "video", "Video upload rules"),
                PlatformRule("tt_desc", "tiktok", "description", "Description rules"),
            ],
        }
        for platform, rules in defaults.items():
            self._rules[platform] = rules

    def get_rules(self, platform: str) -> List[PlatformRule]:
        return list(self._rules.get(platform.lower(), []))

    def add_rule(self, rule: PlatformRule) -> None:
        platform = rule.platform.lower()
        if platform not in self._rules:
            self._rules[platform] = []
        self._rules[platform].append(rule)

    def get_rule(self, rule_id: str) -> Optional[PlatformRule]:
        for rules in self._rules.values():
            for rule in rules:
                if rule.rule_id == rule_id:
                    return rule
        return None

    def get_all_platforms(self) -> List[str]:
        return sorted(self._rules.keys())

    def remove_rule(self, rule_id: str) -> bool:
        for platform in self._rules:
            self._rules[platform] = [r for r in self._rules[platform] if r.rule_id != rule_id]
        return True

    def get_rules_count(self, platform: str = "") -> int:
        if platform:
            return len(self._rules.get(platform.lower(), []))
        return sum(len(rules) for rules in self._rules.values())
