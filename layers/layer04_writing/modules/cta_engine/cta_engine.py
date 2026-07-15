"""CTA Engine — Platform-specific calls-to-action."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


PLATFORM_CTAS = {
    "facebook": [
        "Comment below and let us know! 👇", "Share this with someone who needs it!",
        "Tag a friend who should see this!", "Drop a 🔥 if you agree!",
        "What do you think? Tell us in the comments!",
    ],
    "instagram": [
        "Double tap if you agree! ❤️", "Save this for later! 📌",
        "Share to your story!", "Tag someone who needs this! 🏷️",
        "Comment your thoughts below! 💬",
    ],
    "twitter": [
        "RT if you agree 🔄", "What's your take? Reply below 👇",
        "Bookmark this thread 🔖", "Follow for more insights!",
        "Share this with your network!",
    ],
    "linkedin": [
        "What are your thoughts on this? Let's discuss.", "Share your experience in the comments.",
        "Repost if you found this valuable.", "Connect with me for more insights.",
        "What would you add to this list?",
    ],
    "tiktok": [
        "Follow for more! 🔥", "Duet this if you agree!",
        "Comment your answer! 👇", "Save this for later! 📌",
        "Share with a friend!",
    ],
    "youtube": [
        "Subscribe for more content like this!", "Hit the bell icon! 🔔",
        "Leave a comment below!", "Like if this helped you!",
        "Share with someone who needs this!",
    ],
}

GOAL_CTA_MAP = {
    "educate": ["learn_more", "comment", "share"],
    "entertain": ["share", "comment", "engage"],
    "inspire": ["share", "comment", "follow"],
    "promote": ["visit", "subscribe", "learn_more"],
    "engage": ["comment", "share", "poll"],
}


class CTAResult:
    """Generated CTA with metadata."""
    __slots__ = ("cta_text", "cta_type", "platform", "goal", "alternatives")

    def __init__(self) -> None:
        self.cta_text = ""
        self.cta_type = ""
        self.platform = ""
        self.goal = ""
        self.alternatives: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cta_text": self.cta_text,
            "cta_type": self.cta_type,
            "platform": self.platform,
            "goal": self.goal,
            "alternatives": self.alternatives,
        }


class CTAGenerator:
    """Generates platform-specific calls-to-action."""

    def __init__(self) -> None:
        self._gen_count = 0

    def generate(self, platform: str = "facebook", goal: str = "engage",
                 custom_cta: Optional[str] = None) -> CTAResult:
        """Generate a CTA for the platform and goal."""
        result = CTAResult()
        result.platform = platform
        result.goal = goal

        if custom_cta:
            result.cta_text = custom_cta
            result.cta_type = "custom"
        else:
            platform_ctas = PLATFORM_CTAS.get(platform, PLATFORM_CTAS["facebook"])
            result.cta_text = platform_ctas[0]
            result.cta_type = "platform_default"
            result.alternatives = platform_ctas[1:3]

        self._gen_count += 1
        return result

    def generate_batch(self, platform: str = "facebook", count: int = 3) -> List[CTAResult]:
        """Generate multiple CTAs."""
        results: List[CTAResult] = []
        platform_ctas = PLATFORM_CTAS.get(platform, PLATFORM_CTAS["facebook"])
        for i in range(min(count, len(platform_ctas))):
            r = CTAResult()
            r.cta_text = platform_ctas[i]
            r.cta_type = "platform_default"
            r.platform = platform
            results.append(r)
        return results

    def append_to_content(self, content: str, cta: CTAResult) -> str:
        """Append CTA to content."""
        return f"{content.rstrip()}\n\n{cta.cta_text}"

    @property
    def generation_count(self) -> int:
        return self._gen_count
