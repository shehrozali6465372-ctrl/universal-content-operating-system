"""StyleLibrary — Curated writing styles for every platform and content type.

Stores pre-built style configurations that the Variation Engine uses
to generate prompt variants. Each style has hooks, CTAs, tone guidelines,
and platform-specific rules.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional


# ── Built-in Style Definitions ──

_BUILTIN_STYLES: Dict[str, Dict[str, Any]] = {
    # ── Facebook Styles ──
    "facebook_educational": {
        "platform": "facebook", "category": "educational",
        "description": "Educational posts with value-driven hooks",
        "hooks": [
            "Did you know {topic}?",
            "Here's what most people get wrong about {topic}:",
            "{statistic} of people don't know this about {topic}.",
            "Stop scrolling — this will change how you think about {topic}.",
            "I spent 3 years learning about {topic}. Here's what I found:",
        ],
        "ctas": [
            "What do you think? Drop your opinion below 👇",
            "Save this post for later! 🔖",
            "Tag someone who needs to see this!",
            "Share your experience in the comments!",
        ],
        "tone_guidelines": "Professional yet approachable. Use emojis sparingly. Break long text into short paragraphs.",
        "word_count_range": (150, 500),
        "hashtag_count": (3, 8),
        "image_style": "clean, minimal, data-driven infographic",
    },
    "facebook_engaging": {
        "platform": "facebook", "category": "engaging",
        "description": "High-engagement posts with controversial takes",
        "hooks": [
            "Unpopular opinion: {topic} is overrated.",
            "I'm going to say what nobody else will about {topic}.",
            "🔥 Hot take on {topic} — fight me in the comments.",
            "This {topic} advice is costing you money.",
            "Everyone is wrong about {topic}. Here's why:",
        ],
        "ctas": [
            "Agree or disagree? Let me know! 🔥",
            "Drop a 🔥 if this hit different!",
            "What's YOUR take? Comment below!",
            "Share this if you agree!",
        ],
        "tone_guidelines": "Bold, opinionated, slightly controversial. Use line breaks. End with question.",
        "word_count_range": (100, 300),
        "hashtag_count": (1, 5),
        "image_style": "bold text overlay, high contrast",
    },
    # ── Instagram Styles ──
    "instagram_carousel": {
        "platform": "instagram", "category": "educational",
        "description": "Carousel-style educational content",
        "hooks": [
            "Swipe to learn about {topic} 👉",
            "5 things about {topic} you need to know →",
            "Save this guide on {topic}! 📌",
            "The ultimate {topic} cheat sheet:",
        ],
        "ctas": [
            "Save this for later! 📌",
            "Share with someone who needs this!",
            "Follow for more {topic} tips!",
            "Comment 'GUIDE' and I'll send you the full version!",
        ],
        "tone_guidelines": "Visual-first. Short punchy text. Each slide = one idea. Use emojis as bullet points.",
        "word_count_range": (50, 150),
        "hashtag_count": (15, 30),
        "image_style": "branded carousel, consistent colors, large text",
    },
    "instagram_reels": {
        "platform": "instagram", "category": "entertainment",
        "description": "Reels-optimized short-form content",
        "hooks": [
            "POV: You just discovered {topic}",
            "Wait for it... {topic} edition 🤯",
            "Things about {topic} that make no sense:",
            "This {topic} hack changed my life:",
        ],
        "ctas": [
            "Follow for more! ➡️",
            "Save this! 🔖",
            "Tag a friend who needs this!",
            "Part 2? Comment 'YES'!",
        ],
        "tone_guidelines": "Casual, fast-paced, visual. First 3 seconds = hook. Text overlays.",
        "word_count_range": (30, 80),
        "hashtag_count": (5, 15),
        "image_style": "vertical video, dynamic, text overlays",
    },
    # ── LinkedIn Styles ──
    "linkedin_thought_leadership": {
        "platform": "linkedin", "category": "thought_leadership",
        "description": "Professional thought leadership",
        "hooks": [
            "After 10 years in {topic}, here's what I've learned:",
            "The biggest mistake I see in {topic}:",
            "I just had a breakthrough about {topic}. Let me explain:",
            "The future of {topic} is not what you think.",
            "Here's an uncomfortable truth about {topic}:",
        ],
        "ctas": [
            "What's your experience? I'd love to hear.",
            "Agree? Repost to share with your network.",
            "Follow me for daily insights on {topic}.",
            "What would you add to this list?",
        ],
        "tone_guidelines": "Professional, authoritative, personal anecdotes. Use line breaks. Story-driven.",
        "word_count_range": (150, 400),
        "hashtag_count": (3, 8),
        "image_style": "professional headshot or clean graphic",
    },
    # ── X/Twitter Styles ──
    "x_thread": {
        "platform": "x", "category": "educational",
        "description": "Thread-style educational content",
        "hooks": [
            "🧵 Here's everything I know about {topic} (thread):",
            "I studied {topic} for 6 months. Here are 10 things I learned:",
            "The {topic} space is broken. Here's how to fix it:",
            "STOP scrolling. This thread will change your {topic} game:",
        ],
        "ctas": [
            "♻️ Repost the first tweet to help others!",
            "Follow me @{username} for more threads!",
            "Which point resonated most? Reply!",
            "Bookmark this thread 🔖",
        ],
        "tone_guidelines": "Concise. One idea per tweet. Use numbers. Thread format.",
        "word_count_range": (20, 60),
        "hashtag_count": (1, 3),
        "image_style": "minimal, text-focused, thread format",
    },
    # ── YouTube Styles ──
    "youtube_educational": {
        "platform": "youtube", "category": "educational",
        "description": "Educational video description + script hooks",
        "hooks": [
            "In this video, I'm going to show you exactly how to {topic}.",
            "What if I told you everything you know about {topic} is wrong?",
            "This one {topic} trick saved me 100+ hours:",
            "I tested {topic} for 30 days. Here's what happened:",
        ],
        "ctas": [
            "Smash that subscribe button for more {topic} content!",
            "Drop a comment below with your biggest {topic} challenge!",
            "Watch the next video: [link]",
            "Like this video if it helped you!",
        ],
        "tone_guidelines": "Conversational, energetic. Front-load value. Use timestamps.",
        "word_count_range": (200, 800),
        "hashtag_count": (5, 15),
        "image_style": "thumbnail-optimized, face + bold text",
    },
    # ── TikTok Styles ──
    "tiktok_viral": {
        "platform": "tiktok", "category": "entertainment",
        "description": "Viral-optimized short content",
        "hooks": [
            "You won't believe what {topic} does 👀",
            "POV: You finally understand {topic}",
            "Things about {topic} they don't tell you:",
            "This {topic} hack is illegal how good it is 🤫",
        ],
        "ctas": [
            "Follow for Part 2!",
            "Comment 'MORE' for the full breakdown!",
            "Duet this with your reaction!",
            "Share with someone who needs to see this!",
        ],
        "tone_guidelines": "Ultra-casual, trend-aware. First 1 second = hook. Fast cuts.",
        "word_count_range": (20, 60),
        "hashtag_count": (3, 8),
        "image_style": "vertical, trend-driven, face + text",
    },
}


class StyleLibrary:
    """Manages writing styles for all platforms and content types."""

    def __init__(self) -> None:
        self._styles: Dict[str, Dict[str, Any]] = dict(_BUILTIN_STYLES)
        self._custom_count: int = 0

    def get_style(self, style_name: str) -> Dict[str, Any]:
        """Get a specific style configuration."""
        if style_name not in self._styles:
            return self._default_style()
        return dict(self._styles[style_name])

    def list_styles(self, platform: Optional[str] = None) -> List[str]:
        """List available style names, optionally filtered by platform."""
        if platform:
            return [k for k, v in self._styles.items() if v.get("platform") == platform]
        return list(self._styles.keys())

    def add_style(self, name: str, config: Dict[str, Any]) -> None:
        """Add a custom style."""
        self._styles[name] = config
        self._custom_count += 1

    def remove_style(self, name: str) -> bool:
        """Remove a style (only custom styles)."""
        if name in _BUILTIN_STYLES:
            return False
        if name in self._styles:
            del self._styles[name]
            return True
        return False

    def get_random_hook(self, style_name: str) -> str:
        """Get a random hook template from a style."""
        import random
        style = self.get_style(style_name)
        hooks = style.get("hooks", ["Tell me about {topic}."])
        return random.choice(hooks)

    def get_random_cta(self, style_name: str) -> str:
        """Get a random CTA template from a style."""
        import random
        style = self.get_style(style_name)
        ctas = style.get("ctas", ["What do you think?"])
        return random.choice(ctas)

    def get_platform_styles(self, platform: str) -> List[str]:
        """Get all styles for a specific platform."""
        return self.list_styles(platform)

    def get_style_count(self) -> int:
        """Total number of styles."""
        return len(self._styles)

    def _default_style(self) -> Dict[str, Any]:
        return {
            "platform": "facebook", "category": "general",
            "description": "Default general-purpose style",
            "hooks": ["Let's talk about {topic}."],
            "ctas": ["What do you think?"],
            "tone_guidelines": "Professional, clear, engaging.",
            "word_count_range": (100, 300),
            "hashtag_count": (3, 5),
            "image_style": "clean, professional",
        }
