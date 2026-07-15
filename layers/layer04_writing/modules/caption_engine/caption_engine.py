"""Caption Engine — Platform-specific caption generation."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


PLATFORM_CAPTION_STYLE = {
    "facebook": {"max_length": 63206, "style": "conversational", "line_breaks": True},
    "instagram": {"max_length": 2200, "style": "visual_story", "line_breaks": True},
    "twitter": {"max_length": 280, "style": "concise", "line_breaks": False},
    "linkedin": {"max_length": 3000, "style": "professional", "line_breaks": True},
    "tiktok": {"max_length": 2200, "style": "trendy", "line_breaks": False},
    "youtube": {"max_length": 5000, "style": "descriptive", "line_breaks": True},
    "pinterest": {"max_length": 500, "style": "keyword_rich", "line_breaks": False},
    "threads": {"max_length": 500, "style": "casual", "line_breaks": False},
    "reddit": {"max_length": 40000, "style": "detailed", "line_breaks": True},
    "medium": {"max_length": 25000, "style": "article", "line_breaks": True},
}


class CaptionResult:
    """Generated caption with metadata."""
    __slots__ = ("caption", "platform", "word_count", "char_count",
                 "style", "metadata")

    def __init__(self, caption: str = "", platform: str = "facebook") -> None:
        self.caption = caption
        self.platform = platform
        self.word_count = len(caption.split())
        self.char_count = len(caption)
        self.style = PLATFORM_CAPTION_STYLE.get(platform, {}).get("style", "generic")
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "caption": self.caption,
            "platform": self.platform,
            "word_count": self.word_count,
            "char_count": self.char_count,
            "style": self.style,
        }


class CaptionEngine:
    """Generates platform-optimized captions."""

    def __init__(self) -> None:
        self._gen_count = 0

    def generate(self, draft: str, platform: str = "facebook",
                 style_override: Optional[str] = None) -> CaptionResult:
        """Generate an optimized caption from draft content."""
        spec = PLATFORM_CAPTION_STYLE.get(platform, {})
        max_len = spec.get("max_length", 2000)
        style = style_override or spec.get("style", "generic")

        # Truncate if needed
        caption = draft
        if len(caption) > max_len:
            caption = caption[:max_len - 3] + "..."

        # Apply style formatting
        caption = self._apply_style(caption, style, platform)

        result = CaptionResult(caption=caption, platform=platform)
        result.style = style
        self._gen_count += 1
        return result

    def generate_multi_platform(self, draft: str,
                                 platforms: Optional[List[str]] = None) -> List[CaptionResult]:
        """Generate captions for multiple platforms."""
        plats = platforms or ["facebook", "instagram", "twitter", "linkedin"]
        return [self.generate(draft, p) for p in plats]

    def _apply_style(self, text: str, style: str, platform: str) -> str:
        if style == "concise" and platform == "twitter":
            sentences = text.split('. ')
            if len(sentences) > 2:
                text = '. '.join(sentences[:2]) + '.'
        elif style == "professional":
            text = text.replace("!", ".").replace("?", "?")
        elif style == "trendy":
            text = text.rstrip()
        return text.strip()

    @property
    def generation_count(self) -> int:
        return self._gen_count
