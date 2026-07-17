"""CTAEngine — Generate platform-specific calls to action."""
from __future__ import annotations
import itertools
from typing import Any, Dict, List

_CTA_COUNTER = itertools.count(1)


class CTA:
    """A call to action."""

    __slots__ = ("cta_id", "text", "cta_type", "platform", "position")

    def __init__(self, text: str = "", cta_type: str = "") -> None:
        self.cta_id: str = f"cta_{next(_CTA_COUNTER)}"
        self.text = text
        self.cta_type = cta_type
        self.platform: str = ""
        self.position: str = "end"

    def to_dict(self) -> Dict[str, Any]:
        return {"cta_id": self.cta_id, "text": self.text,
                "cta_type": self.cta_type, "platform": self.platform}


PLATFORM_CTAS = {
    "facebook": ["Like & Share if you agree!", "Comment your thoughts below.", "Follow for more insights."],
    "instagram": ["Double tap if you agree!", "Save this for later.", "Tag a friend who needs this."],
    "x": ["Retweet if useful.", "Reply with your take.", "Bookmark for later."],
    "linkedin": ["What are your thoughts?", "Share your experience.", "Follow for industry insights."],
    "youtube": ["Subscribe for more!", "Hit the bell icon.", "Comment your questions below."],
    "tiktok": ["Follow for more!", "Comment Part 2!", "Share with a friend."],
    "threads": ["Reply with your thoughts.", "Repost if you agree.", "Follow for more."],
}


class CTAEngine:
    """Generate platform-specific calls to action."""

    def __init__(self) -> None:
        self._ctas: List[CTA] = []
        self._custom_ctas: Dict[str, List[str]] = {}

    def generate(self, platform: str = "facebook", count: int = 3) -> List[CTA]:
        templates = self._custom_ctas.get(platform, PLATFORM_CTAS.get(platform, PLATFORM_CTAS["facebook"]))
        generated = []
        for text in templates[:count]:
            cta = CTA(text, "engagement")
            cta.platform = platform
            self._ctas.append(cta)
            generated.append(cta)
        return generated

    def add_custom_cta(self, platform: str, text: str) -> None:
        if platform not in self._custom_ctas:
            self._custom_ctas[platform] = []
        self._custom_ctas[platform].append(text)

    def get_ctas(self, platform: str = "", limit: int = 10) -> List[CTA]:
        results = self._ctas
        if platform:
            results = [c for c in results if c.platform == platform]
        return results[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        platforms = {}
        for c in self._ctas:
            platforms[c.platform] = platforms.get(c.platform, 0) + 1
        return {"total": len(self._ctas), "by_platform": platforms}
