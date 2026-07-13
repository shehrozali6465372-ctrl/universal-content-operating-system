"""
Content Analyzer
Layer 2: Research Engine — Module 3

Analyzes competitor content patterns:
- Topic distribution
- Format preferences
- Hashtag usage patterns
- Content themes and clustering
"""

from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple
from layers.layer02_research.modules.competitor_analysis.competitor_profile import CompetitorProfile


class ContentPost:
    """Represents a single analyzed post from a competitor."""

    __slots__ = (
        "post_id", "content_type", "topic", "text",
        "hashtags", "likes", "comments", "shares",
        "posted_at", "has_image", "has_video", "has_link",
        "word_count", "sentiment",
    )

    def __init__(
        self,
        post_id: str = "",
        content_type: str = "text",
        topic: str = "general",
        text: str = "",
        hashtags: Optional[List[str]] = None,
        likes: int = 0,
        comments: int = 0,
        shares: int = 0,
        posted_at: str = "",
        has_image: bool = False,
        has_video: bool = False,
        has_link: bool = False,
        sentiment: str = "neutral",
    ):
        self.post_id = post_id
        self.content_type = content_type
        self.topic = topic
        self.text = text
        self.hashtags = hashtags or []
        self.likes = max(0, likes)
        self.comments = max(0, comments)
        self.shares = max(0, shares)
        self.posted_at = posted_at
        self.has_image = has_image
        self.has_video = has_video
        self.has_link = has_link
        self.word_count = len(text.split()) if text else 0
        self.sentiment = sentiment

    @property
    def total_engagement(self) -> int:
        return self.likes + self.comments + self.shares


class ContentAnalyzer:
    """Analyze content patterns of a competitor."""

    def __init__(self):
        self._posts: Dict[str, List[ContentPost]] = {}

    def add_posts(self, competitor_id: str, posts: List[ContentPost]):
        """Store posts for a competitor."""
        if competitor_id not in self._posts:
            self._posts[competitor_id] = []
        self._posts[competitor_id].extend(posts)

    def get_posts(self, competitor_id: str) -> List[ContentPost]:
        return list(self._posts.get(competitor_id, []))

    def analyze_topics(self, competitor_id: str) -> Dict[str, int]:
        """Count topic distribution."""
        posts = self.get_posts(competitor_id)
        return dict(Counter(p.topic for p in posts).most_common())

    def analyze_formats(self, competitor_id: str) -> Dict[str, int]:
        """Count content type distribution."""
        posts = self.get_posts(competitor_id)
        return dict(Counter(p.content_type for p in posts).most_common())

    def analyze_hashtags(self, competitor_id: str, top_n: int = 20) -> List[Tuple[str, int]]:
        """Get top hashtags used."""
        posts = self.get_posts(competitor_id)
        counter = Counter()
        for p in posts:
            counter.update(p.hashtags)
        return counter.most_common(top_n)

    def analyze_media_usage(self, competitor_id: str) -> Dict[str, float]:
        """Analyze media usage percentages."""
        posts = self.get_posts(competitor_id)
        if not posts:
            return {"image_pct": 0, "video_pct": 0, "link_pct": 0, "text_only_pct": 0}
        total = len(posts)
        images = sum(1 for p in posts if p.has_image)
        videos = sum(1 for p in posts if p.has_video)
        links = sum(1 for p in posts if p.has_link)
        text_only = sum(1 for p in posts if not p.has_image and not p.has_video and not p.has_link)
        return {
            "image_pct": round(images / total * 100, 1),
            "video_pct": round(videos / total * 100, 1),
            "link_pct": round(links / total * 100, 1),
            "text_only_pct": round(text_only / total * 100, 1),
        }

    def analyze_sentiment(self, competitor_id: str) -> Dict[str, int]:
        """Sentiment distribution."""
        posts = self.get_posts(competitor_id)
        return dict(Counter(p.sentiment for p in posts).most_common())

    def get_top_posts(self, competitor_id: str, count: int = 10) -> List[ContentPost]:
        """Get highest engagement posts."""
        posts = self.get_posts(competitor_id)
        return sorted(posts, key=lambda p: p.total_engagement, reverse=True)[:count]

    def get_average_word_count(self, competitor_id: str) -> float:
        """Average word count per post."""
        posts = self.get_posts(competitor_id)
        if not posts:
            return 0.0
        return round(sum(p.word_count for p in posts) / len(posts), 1)

    def detect_content_themes(self, competitor_id: str) -> Dict[str, Dict]:
        """Cluster posts into themes with engagement stats."""
        posts = self.get_posts(competitor_id)
        themes: Dict[str, List[ContentPost]] = defaultdict(list)
        for p in posts:
            themes[p.topic].append(p)

        result = {}
        for topic, group in themes.items():
            eng = [p.total_engagement for p in group]
            result[topic] = {
                "post_count": len(group),
                "avg_engagement": round(sum(eng) / len(eng), 1) if eng else 0,
                "max_engagement": max(eng) if eng else 0,
                "media_types": dict(Counter(
                    "image" if p.has_image else "video" if p.has_video else "text"
                    for p in group
                )),
            }
        return result

    def update_profile_from_posts(self, profile: CompetitorProfile) -> CompetitorProfile:
        """Auto-fill profile fields from analyzed posts."""
        posts = self.get_posts(profile.competitor_id)
        if not posts:
            return profile

        # Topics
        topic_counts = self.analyze_topics(profile.competitor_id)
        profile.top_topics = list(topic_counts.keys())[:10]

        # Formats
        format_counts = self.analyze_formats(profile.competitor_id)
        profile.top_formats = list(format_counts.keys())[:5]

        # Hashtags
        top_tags = self.analyze_hashtags(profile.competitor_id, top_n=15)
        profile.top_hashtags = [tag for tag, _ in top_tags]

        # Engagement averages
        total_posts = len(posts)
        profile.avg_likes = round(sum(p.likes for p in posts) / total_posts, 1)
        profile.avg_comments = round(sum(p.comments for p in posts) / total_posts, 1)
        profile.avg_shares = round(sum(p.shares for p in posts) / total_posts, 1)
        if profile.avg_likes > 0:
            profile.avg_engagement_rate = round(
                (profile.avg_comments + profile.avg_shares) / profile.avg_likes * 100, 2
            )

        # Media
        media = self.analyze_media_usage(profile.competitor_id)
        if media["image_pct"] > 50:
            profile.image_style = "image_heavy"
        elif media["video_pct"] > 50:
            profile.image_style = "video_heavy"
        elif media["text_only_pct"] > 50:
            profile.image_style = "text_focused"
        else:
            profile.image_style = "mixed"

        profile.data_quality = "analyzed"
        profile.updated_at = profile.created_at  # Will be set by manager
        return profile
