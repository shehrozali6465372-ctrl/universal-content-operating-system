"""PlatformAdapter — Convert one article into platform-specific formats.

Features:
- Blog → Full Article (long-form)
- Facebook → Post (with hashtags, CTA)
- Instagram → Caption (short, emoji-rich, hashtags)
- X/Twitter → Thread (280 char chunks)
- YouTube → Community Post
- TikTok → Short Caption
- Pinterest → Pin Description
- LinkedIn → Professional Post
- Platform-specific character limits
- Hashtag optimization per platform
- Emoji strategy per platform
"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, Tuple


# Platform specifications
PLATFORM_SPECS = {
    "wordpress": {
        "max_length": 50000, "supports_images": True, "supports_video": True,
        "supports_html": True, "supports_links": True, "supports_hashtags": False,
        "tone": "professional", "format": "html",
        "emoji_strategy": "minimal",
    },
    "medium": {
        "max_length": 100000, "supports_images": True, "supports_video": True,
        "supports_html": True, "supports_links": True, "supports_hashtags": True,
        "tone": "thoughtful", "format": "markdown",
        "emoji_strategy": "moderate",
    },
    "devto": {
        "max_length": 50000, "supports_images": True, "supports_video": True,
        "supports_html": True, "supports_links": True, "supports_hashtags": True,
        "tone": "technical", "format": "markdown",
        "emoji_strategy": "moderate",
    },
    "hashnode": {
        "max_length": 50000, "supports_images": True, "supports_video": True,
        "supports_html": True, "supports_links": True, "supports_hashtags": True,
        "tone": "technical", "format": "markdown",
        "emoji_strategy": "minimal",
    },
    "facebook": {
        "max_length": 63206, "supports_images": True, "supports_video": True,
        "supports_html": False, "supports_links": True, "supports_hashtags": True,
        "tone": "conversational", "format": "text",
        "emoji_strategy": "moderate", "optimal_length": 400,
        "max_hashtags": 5,
    },
    "instagram": {
        "max_length": 2200, "supports_images": True, "supports_video": True,
        "supports_html": False, "supports_links": False, "supports_hashtags": True,
        "tone": "casual", "format": "text",
        "emoji_strategy": "heavy", "optimal_length": 150,
        "max_hashtags": 30, "optimal_hashtags": 15,
    },
    "x": {
        "max_length": 280, "supports_images": True, "supports_video": True,
        "supports_html": False, "supports_links": True, "supports_hashtags": True,
        "tone": "concise", "format": "text",
        "emoji_strategy": "minimal", "supports_threads": True,
        "max_hashtags": 3,
    },
    "tiktok": {
        "max_length": 2200, "supports_images": False, "supports_video": True,
        "supports_html": False, "supports_links": False, "supports_hashtags": True,
        "tone": "trendy", "format": "text",
        "emoji_strategy": "heavy", "optimal_length": 300,
        "max_hashtags": 10,
    },
    "youtube": {
        "max_length": 10000, "supports_images": True, "supports_video": True,
        "supports_html": False, "supports_links": True, "supports_hashtags": True,
        "tone": "engaging", "format": "text",
        "emoji_strategy": "moderate", "max_hashtags": 15,
    },
    "pinterest": {
        "max_length": 500, "supports_images": True, "supports_video": True,
        "supports_html": False, "supports_links": True, "supports_hashtags": True,
        "tone": "inspirational", "format": "text",
        "emoji_strategy": "moderate", "max_hashtags": 20,
        "optimal_length": 200,
    },
    "linkedin": {
        "max_length": 3000, "supports_images": True, "supports_video": True,
        "supports_html": False, "supports_links": True, "supports_hashtags": True,
        "tone": "professional", "format": "text",
        "emoji_strategy": "minimal", "optimal_length": 1500,
        "max_hashtags": 5,
    },
    "telegram": {
        "max_length": 4096, "supports_images": True, "supports_video": True,
        "supports_html": True, "supports_links": True, "supports_hashtags": True,
        "tone": "informative", "format": "html",
        "emoji_strategy": "moderate",
    },
    "reddit": {
        "max_length": 40000, "supports_images": True, "supports_video": True,
        "supports_html": True, "supports_links": True, "supports_hashtags": False,
        "tone": "authentic", "format": "markdown",
        "emoji_strategy": "minimal",
    },
    "blogger": {
        "max_length": 50000, "supports_images": True, "supports_video": True,
        "supports_html": True, "supports_links": True, "supports_hashtags": False,
        "tone": "casual", "format": "html",
        "emoji_strategy": "minimal",
    },
    "custom_website": {
        "max_length": 100000, "supports_images": True, "supports_video": True,
        "supports_html": True, "supports_links": True, "supports_hashtags": False,
        "tone": "custom", "format": "html",
        "emoji_strategy": "none",
    },
}


class PlatformAdapter:
    """Convert content to platform-specific formats."""

    def __init__(self):
        self._specs = PLATFORM_SPECS

    def get_spec(self, platform: str) -> Dict[str, Any]:
        """Get platform specifications."""
        return self._specs.get(platform.lower(), self._specs["custom_website"])

    def adapt(self, content: str, source_platform: str, target_platform: str,
              metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Adapt content from one platform format to another.

        Args:
            content: Original content
            source_platform: Source platform format
            target_platform: Target platform format
            metadata: Additional metadata (title, hashtags, etc)

        Returns:
            Dict with adapted content and metadata
        """
        metadata = metadata or {}
        spec = self.get_spec(target_platform)
        max_len = spec["max_length"]

        # Extract title and body
        title = metadata.get("title", "")
        body = content
        if title and content.startswith(title):
            body = content[len(title):].strip()

        # Adapt based on target platform
        if target_platform in ("facebook", "linkedin", "telegram"):
            adapted = self._adapt_social_post(body, title, spec, metadata)
        elif target_platform == "instagram":
            adapted = self._adapt_instagram(body, title, spec, metadata)
        elif target_platform == "x":
            adapted = self._adapt_twitter_thread(body, title, spec, metadata)
        elif target_platform == "tiktok":
            adapted = self._adapt_tiktok(body, title, spec, metadata)
        elif target_platform == "pinterest":
            adapted = self._adapt_pinterest(body, title, spec, metadata)
        elif target_platform == "youtube":
            adapted = self._adapt_youtube(body, title, spec, metadata)
        elif target_platform in ("wordpress", "medium", "devto", "hashnode", "blogger", "custom_website"):
            adapted = self._adapt_blog(body, title, spec, metadata)
        else:
            adapted = self._adapt_generic(body, max_len)

        return {
            "platform": target_platform,
            "content": adapted["content"],
            "title": adapted.get("title", title),
            "hashtags": adapted.get("hashtags", []),
            "character_count": len(adapted["content"]),
            "max_length": max_len,
            "within_limit": len(adapted["content"]) <= max_len,
            "metadata": adapted.get("metadata", {}),
        }

    def adapt_to_all(self, content: str, platforms: List[str],
                     metadata: Dict[str, Any] = None) -> Dict[str, Dict]:
        """Adapt content to multiple platforms at once."""
        return {p: self.adapt(content, "generic", p, metadata) for p in platforms}

    def _adapt_social_post(self, body: str, title: str, spec: Dict, metadata: Dict) -> Dict:
        """Adapt for Facebook/LinkedIn/Telegram."""
        hashtags = metadata.get("hashtags", [])
        emoji = spec.get("emoji_strategy", "moderate")

        # Build post
        parts = []
        if title:
            parts.append(f"📢 {title}" if emoji != "none" else title)

        # Truncate body
        max_body = spec["max_length"] - len(title) - 100
        truncated = body[:max_body].strip()
        parts.append(truncated)

        # Add hashtags
        max_tags = spec.get("max_hashtags", 5)
        if hashtags and spec["supports_hashtags"]:
            tag_str = " ".join(f"#{t}" for t in hashtags[:max_tags])
            parts.append(f"\n\n{tag_str}")

        # Add CTA
        if metadata.get("cta"):
            parts.append(f"\n\n{metadata['cta']}")

        content = "\n".join(parts)
        if len(content) > spec["max_length"]:
            content = content[:spec["max_length"] - 3] + "..."

        return {"content": content, "hashtags": hashtags[:max_tags], "title": title}

    def _adapt_instagram(self, body: str, title: str, spec: Dict, metadata: Dict) -> Dict:
        """Adapt for Instagram."""
        hashtags = metadata.get("hashtags", [])
        optimal = spec.get("optimal_length", 150)

        # Instagram caption: hook + content + hashtags
        hook = body[:optimal].strip()
        if len(body) > optimal:
            # Find last sentence boundary
            for sep in [". ", "! ", "? "]:
                idx = hook.rfind(sep)
                if idx > optimal * 0.5:
                    hook = hook[:idx + 1]
                    break

        max_tags = spec.get("optimal_hashtags", 15)
        tag_str = " ".join(f"#{t}" for t in hashtags[:max_tags]) if hashtags else ""

        content = hook
        if tag_str:
            content += f"\n\n{tag_str}"

        # Ensure within limit
        if len(content) > spec["max_length"]:
            content = content[:spec["max_length"] - 3] + "..."

        return {"content": content, "hashtags": hashtags[:max_tags], "title": title}

    def _adapt_twitter_thread(self, body: str, title: str, spec: Dict, metadata: Dict) -> Dict:
        """Adapt for X/Twitter thread."""
        max_len = 280
        hashtags = metadata.get("hashtags", [])

        # Split into thread tweets
        tweets = []
        remaining = body

        # First tweet: hook
        hook = f"🧵 {title}\n\n" if title else ""
        first_tweet = hook + remaining[:max_len - len(hook)]
        tweets.append(first_tweet.strip())
        remaining = remaining[len(first_tweet) - len(hook):]

        # Remaining tweets
        while remaining and len(remaining) > 0:
            tweet = remaining[:max_len].strip()
            if not tweet:
                break
            if len(remaining) > max_len:
                for sep in ["\n\n", "\n", ". ", " "]:
                    idx = tweet.rfind(sep)
                    if idx > max_len * 0.5:
                        tweet = tweet[:idx + len(sep)].strip()
                        break
            tweets.append(tweet)
            consumed = len(tweet)
            if consumed == 0:
                break
            remaining = remaining[consumed:]

        # Add hashtags to last tweet
        if hashtags:
            tag_str = " ".join(f"#{t}" for t in hashtags[:3])
            last = tweets[-1]
            if len(last) + len(tag_str) + 2 <= max_len:
                tweets[-1] = f"{last}\n\n{tag_str}"

        thread_str = " ||| ".join(tweets)
        return {"content": thread_str, "hashtags": hashtags[:3], "title": title,
                "metadata": {"is_thread": len(tweets) > 1, "tweet_count": len(tweets)}}

    def _adapt_tiktok(self, body: str, title: str, spec: Dict, metadata: Dict) -> Dict:
        """Adapt for TikTok."""
        hashtags = metadata.get("hashtags", [])

        # TikTok: short, catchy caption
        caption = body[:300].strip()
        if title:
            caption = f"{title}\n\n{caption}"

        max_tags = spec.get("max_hashtags", 10)
        if hashtags:
            tag_str = " ".join(f"#{t}" for t in hashtags[:max_tags])
            caption = f"{caption}\n\n{tag_str}"

        if len(caption) > spec["max_length"]:
            caption = caption[:spec["max_length"] - 3] + "..."

        return {"content": caption, "hashtags": hashtags[:max_tags], "title": title}

    def _adapt_pinterest(self, body: str, title: str, spec: Dict, metadata: Dict) -> Dict:
        """Adapt for Pinterest."""
        hashtags = metadata.get("hashtags", [])

        # Pinterest: short description with keywords
        desc = body[:200].strip()
        if title:
            desc = f"{title}: {desc}"

        max_tags = spec.get("max_hashtags", 20)
        if hashtags:
            tag_str = " ".join(f"#{t}" for t in hashtags[:max_tags])
            desc = f"{desc}\n\n{tag_str}"

        if len(desc) > spec["max_length"]:
            desc = desc[:spec["max_length"] - 3] + "..."

        return {"content": desc, "hashtags": hashtags[:max_tags], "title": title}

    def _adapt_youtube(self, body: str, title: str, spec: Dict, metadata: Dict) -> Dict:
        """Adapt for YouTube Community Post."""
        hashtags = metadata.get("hashtags", [])

        # YouTube community post
        post = body[:1000].strip()
        if title:
            post = f"📢 {title}\n\n{post}"

        max_tags = spec.get("max_hashtags", 15)
        if hashtags:
            tag_str = " ".join(f"#{t}" for t in hashtags[:max_tags])
            post = f"{post}\n\n{tag_str}"

        if len(post) > spec["max_length"]:
            post = post[:spec["max_length"] - 3] + "..."

        return {"content": post, "hashtags": hashtags[:max_tags], "title": title}

    def _adapt_blog(self, body: str, title: str, spec: Dict, metadata: Dict) -> Dict:
        """Adapt for blog platforms."""
        fmt = spec.get("format", "markdown")

        # Blog: full article
        content = body
        if title:
            if fmt == "markdown":
                content = f"# {title}\n\n{body}"
            elif fmt == "html":
                content = f"<h1>{title}</h1>\n\n{body}"

        # Add featured image if provided
        if metadata.get("featured_image"):
            img = metadata["featured_image"]
            if fmt == "markdown":
                content += f"\n\n![{title}]({img})"
            elif fmt == "html":
                content += f'\n\n<img src="{img}" alt="{title}">'

        return {"content": content, "title": title, "hashtags": []}

    def _adapt_generic(self, body: str, max_len: int) -> Dict:
        """Generic adaptation."""
        content = body[:max_len].strip()
        return {"content": content, "title": "", "hashtags": []}

    def validate(self, content: str, platform: str) -> Dict[str, Any]:
        """Validate content for a platform."""
        spec = self.get_spec(platform)
        length = len(content)
        max_len = spec["max_length"]

        issues = []
        if length > max_len:
            issues.append(f"Content exceeds {max_len} chars by {length - max_len}")

        return {
            "platform": platform,
            "valid": len(issues) == 0,
            "length": length,
            "max_length": max_len,
            "issues": issues,
        }

    def get_optimal_hashtags(self, topic: str, platform: str, count: int = 10) -> List[str]:
        """Generate optimal hashtags for a topic and platform."""
        spec = self.get_spec(platform)
        max_tags = spec.get("max_hashtags", 5)

        # Generate from topic keywords
        words = re.findall(r'\w+', topic.lower())
        hashtags = []
        for word in words:
            if len(word) > 3:
                hashtags.append(word)
        # Add common variations
        hashtags.extend(["trending", "viral", "content", "creator"])
        return list(dict.fromkeys(hashtags))[:min(count, max_tags)]

    def stats(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        return {
            "supported_platforms": list(self._specs.keys()),
            "total_platforms": len(self._specs),
        }
