"""Platform Rules — Detailed compliance rules for each platform.

Rules cover: character limits, formatting, media, links, hashtags,
mentions, tone, content type restrictions, and posting guidelines.
"""
from __future__ import annotations
from typing import Any, Dict, List


PLATFORM_RULES: Dict[str, Dict[str, Any]] = {
    "facebook": {
        "max_post_length": 63206,
        "max_comment_length": 8000,
        "max_hashtags": 30,
        "optimal_hashtags": (1, 3),
        "max_mentions": 5,
        "max_link_preview": 1,
        "supports_images": True,
        "supports_video": True,
        "supports_carousel": True,
        "supports_gif": True,
        "supports_polls": True,
        "supports_links": True,
        "max_image_text_ratio": 0.2,
        "no_engagement_bait": True,
        "no_clickbait": True,
        "min_post_length": 10,
        "forbidden_patterns": [
            r"like\s+and\s+share\s+to\s+win",
            r"tag\s+a\s+friend\s+who",
            r"share\s+if\s+you\s+agree",
        ],
        "tone_requirements": [],
        "requires_image": False,
        "optimal_length": (40, 80),
    },
    "instagram": {
        "max_post_length": 2200,
        "max_comment_length": 300,
        "max_hashtags": 30,
        "optimal_hashtags": (3, 10),
        "max_mentions": 5,
        "supports_images": True,
        "supports_video": True,
        "supports_carousel": True,
        "supports_reels": True,
        "supports_stories": True,
        "supports_links": False,
        "max_image_count": 10,
        "image_aspect_ratios": ["1:1", "4:5", "1.91:1"],
        "no_visual_nudity": True,
        "min_post_length": 5,
        "optimal_caption_length": (138, 150),
        "forbidden_patterns": [],
        "requires_hashtags": True,
    },
    "twitter": {
        "max_post_length": 280,
        "max_hashtags": 5,
        "optimal_hashtags": (1, 2),
        "max_mentions": 5,
        "supports_images": True,
        "supports_video": True,
        "supports_polls": True,
        "supports_gif": True,
        "supports_links": True,
        "url_length": 23,
        "max_images": 4,
        "no_engagement_bait": True,
        "min_post_length": 5,
        "optimal_length": (70, 140),
        "forbidden_patterns": [
            r"follow\s+me\s+for\s+follow",
            r"rt\s+to\s+win",
        ],
    },
    "linkedin": {
        "max_post_length": 3000,
        "max_article_length": 110000,
        "max_hashtags": 5,
        "optimal_hashtags": (3, 5),
        "max_mentions": 5,
        "supports_images": True,
        "supports_video": True,
        "supports_document": True,
        "supports_polls": True,
        "supports_links": True,
        "no_all_caps": True,
        "professional_tone": True,
        "min_post_length": 20,
        "optimal_length": (100, 300),
        "forbidden_patterns": [
            r"click\s+bait",
            r"follow\s+for\s+follow",
        ],
    },
    "tiktok": {
        "max_post_length": 2200,
        "max_hashtags": 5,
        "optimal_hashtags": (3, 5),
        "max_mentions": 5,
        "supports_video": True,
        "supports_images": True,
        "supports_livestream": True,
        "max_video_length_seconds": 600,
        "optimal_video_length_seconds": (15, 60),
        "min_post_length": 5,
        "optimal_caption_length": (100, 150),
        "forbidden_patterns": [],
    },
    "youtube": {
        "max_title_length": 100,
        "max_description_length": 5000,
        "max_hashtags": 15,
        "optimal_hashtags": (3, 5),
        "supports_video": True,
        "supports_shorts": True,
        "supports_community_posts": True,
        "max_tags": 500,
        "optimal_title_length": (40, 60),
        "optimal_desc_length": (200, 500),
        "requires_description": True,
        "forbidden_patterns": [],
    },
    "pinterest": {
        "max_description_length": 500,
        "max_hashtags": 20,
        "optimal_hashtags": (5, 8),
        "supports_images": True,
        "supports_video": True,
        "ideal_image_ratio": "2:3",
        "max_board_count": 500,
        "requires_image": True,
        "forbidden_patterns": [],
    },
    "reddit": {
        "max_post_length": 40000,
        "max_title_length": 300,
        "supports_images": True,
        "supports_video": True,
        "supports_polls": True,
        "no_self_promotion_excessive": True,
        "no_spam": True,
        "min_post_length": 20,
        "optimal_title_length": (50, 100),
        "forbidden_patterns": [
            r"upvote\s+if",
            r"please\s+upvote",
            r"like\s+and\s+subscribe",
        ],
    },
    "medium": {
        "max_post_length": 100000,
        "supports_images": True,
        "supports_code_blocks": True,
        "supports_embeds": True,
        "no_plagiarism": True,
        "original_content_required": True,
        "optimal_title_length": (40, 60),
        "optimal_reading_time_minutes": (5, 10),
        "forbidden_patterns": [],
    },
}

# Version tracking for platform rules
RULES_VERSION = "1.0.0"
RULES_LAST_UPDATED = "2025-01-15"


def get_rules(platform: str) -> Dict[str, Any]:
    """Get rules for a specific platform."""
    return PLATFORM_RULES.get(platform.lower(), {})


def get_all_platforms() -> List[str]:
    """Get list of all supported platforms."""
    return list(PLATFORM_RULES.keys())


def get_rules_version() -> str:
    """Get current rules version."""
    return RULES_VERSION
