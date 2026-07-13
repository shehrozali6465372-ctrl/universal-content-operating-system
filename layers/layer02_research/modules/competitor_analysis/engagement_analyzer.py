"""
Engagement Analyzer
Layer 2: Research Engine — Module 3

Deep engagement analysis for competitor content:
- Engagement rate calculation
- Engagement trends over time
- Viral post detection
- Engagement-to-reach ratios
- Comment quality analysis
- Share virality scoring
"""

from collections import defaultdict
from typing import Dict, List, Optional
from layers.layer02_research.modules.competitor_analysis.content_analyzer import ContentPost


class EngagementMetrics:
    """Computed engagement metrics for a competitor."""

    __slots__ = (
        "competitor_id", "total_posts", "total_engagement",
        "avg_engagement_rate", "avg_likes", "avg_comments", "avg_shares",
        "engagement_trend", "viral_posts", "top_engaged_topics",
        "best_performing_format", "engagement_growth_rate",
        "comment_to_like_ratio", "share_to_like_ratio",
        "engagement_volatility",
    )

    def __init__(self, competitor_id: str):
        self.competitor_id = competitor_id
        self.total_posts = 0
        self.total_engagement = 0
        self.avg_engagement_rate = 0.0
        self.avg_likes = 0.0
        self.avg_comments = 0.0
        self.avg_shares = 0.0
        self.engagement_trend = "unknown"
        self.viral_posts: List[str] = []
        self.top_engaged_topics: List[str] = []
        self.best_performing_format = "unknown"
        self.engagement_growth_rate = 0.0
        self.comment_to_like_ratio = 0.0
        self.share_to_like_ratio = 0.0
        self.engagement_volatility = 0.0

    def to_dict(self) -> dict:
        return {
            "competitor_id": self.competitor_id,
            "total_posts": self.total_posts,
            "total_engagement": self.total_engagement,
            "avg_engagement_rate": self.avg_engagement_rate,
            "avg_likes": self.avg_likes,
            "avg_comments": self.avg_comments,
            "avg_shares": self.avg_shares,
            "engagement_trend": self.engagement_trend,
            "viral_posts": self.viral_posts,
            "top_engaged_topics": self.top_engaged_topics,
            "best_performing_format": self.best_performing_format,
            "engagement_growth_rate": self.engagement_growth_rate,
            "comment_to_like_ratio": self.comment_to_like_ratio,
            "share_to_like_ratio": self.share_to_like_ratio,
            "engagement_volatility": self.engagement_volatility,
        }


class EngagementAnalyzer:
    """Deep engagement analysis engine."""

    VIRAL_THRESHOLD_PERCENTILE = 90  # Top 10% posts = viral

    def __init__(self):
        self._metrics: Dict[str, EngagementMetrics] = {}

    def analyze(self, competitor_id: str, posts: List[ContentPost]) -> EngagementMetrics:
        """Full engagement analysis."""
        metrics = EngagementMetrics(competitor_id)

        if not posts:
            self._metrics[competitor_id] = metrics
            return metrics

        metrics.total_posts = len(posts)
        total_eng = sum(p.total_engagement for p in posts)
        metrics.total_engagement = total_eng

        # Averages
        metrics.avg_likes = round(sum(p.likes for p in posts) / len(posts), 1)
        metrics.avg_comments = round(sum(p.comments for p in posts) / len(posts), 1)
        metrics.avg_shares = round(sum(p.shares for p in posts) / len(posts), 1)
        avg_total = total_eng / len(posts)

        # Engagement rate (comments + shares / likes, as percentage)
        if metrics.avg_likes > 0:
            metrics.avg_engagement_rate = round(
                (metrics.avg_comments + metrics.avg_shares) / metrics.avg_likes * 100, 2
            )

        # Ratios
        metrics.comment_to_like_ratio = (
            round(metrics.avg_comments / metrics.avg_likes, 4) if metrics.avg_likes > 0 else 0
        )
        metrics.share_to_like_ratio = (
            round(metrics.avg_shares / metrics.avg_likes, 4) if metrics.avg_likes > 0 else 0
        )

        # Viral posts (top 10%)
        eng_values = sorted([p.total_engagement for p in posts], reverse=True)
        viral_threshold = eng_values[int(len(eng_values) * self.VIRAL_THRESHOLD_PERCENTILE / 100)] if eng_values else 0
        metrics.viral_posts = [
            p.post_id for p in posts if p.total_engagement >= viral_threshold and p.post_id
        ]

        # Topic engagement
        topic_eng: Dict[str, List[int]] = defaultdict(list)
        for p in posts:
            topic_eng[p.topic].append(p.total_engagement)
        topic_avgs = {t: sum(v) / len(v) for t, v in topic_eng.items() if v}
        metrics.top_engaged_topics = [
            t for t, _ in sorted(topic_avgs.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        # Best format
        format_eng: Dict[str, List[int]] = defaultdict(list)
        for p in posts:
            format_eng[p.content_type].append(p.total_engagement)
        format_avgs = {f: sum(v) / len(v) for f, v in format_eng.items() if v}
        if format_avgs:
            metrics.best_performing_format = max(format_avgs, key=format_avgs.get)

        # Trend detection (split posts in half, compare averages)
        mid = len(posts) // 2
        if mid > 0:
            first_half_avg = sum(p.total_engagement for p in posts[:mid]) / mid
            second_half_avg = sum(p.total_engagement for p in posts[mid:]) / (len(posts) - mid)
            if first_half_avg > 0:
                growth = (second_half_avg - first_half_avg) / first_half_avg * 100
                metrics.engagement_growth_rate = round(growth, 2)
                if growth > 10:
                    metrics.engagement_trend = "growing"
                elif growth < -10:
                    metrics.engagement_trend = "declining"
                else:
                    metrics.engagement_trend = "stable"

        # Volatility (standard deviation)
        if len(posts) > 1:
            engs = [p.total_engagement for p in posts]
            mean = sum(engs) / len(engs)
            variance = sum((e - mean) ** 2 for e in engs) / len(engs)
            metrics.engagement_volatility = round(variance ** 0.5, 2)

        self._metrics[competitor_id] = metrics
        return metrics

    def get_metrics(self, competitor_id: str) -> Optional[EngagementMetrics]:
        return self._metrics.get(competitor_id)

    def find_viral_patterns(
        self, competitor_id: str, posts: List[ContentPost]
    ) -> Dict[str, any]:
        """Find common patterns in viral posts."""
        metrics = self._metrics.get(competitor_id)
        if not metrics:
            return {}

        viral_ids = set(metrics.viral_posts)
        viral_posts = [p for p in posts if p.post_id in viral_ids]

        if not viral_posts:
            return {"viral_count": 0}

        return {
            "viral_count": len(viral_posts),
            "avg_word_count": round(sum(p.word_count for p in viral_posts) / len(viral_posts), 1),
            "common_topics": list(defaultdict(int, **{
                t: sum(1 for p in viral_posts if p.topic == t)
                for t in set(p.topic for p in viral_posts)
            }).keys())[:3],
            "media_heavy": sum(1 for p in viral_posts if p.has_image or p.has_video) / len(viral_posts) > 0.5,
            "avg_hashtags": round(sum(len(p.hashtags) for p in viral_posts) / len(viral_posts), 1),
        }

    def compare_engagement(
        self, comp_a: str, comp_b: str
    ) -> Dict[str, any]:
        """Compare engagement between two competitors."""
        ma = self._metrics.get(comp_a)
        mb = self._metrics.get(comp_b)
        if not ma or not mb:
            return {"error": "Missing metrics"}
        return {
            "engagement_rate_diff": round(ma.avg_engagement_rate - mb.avg_engagement_rate, 2),
            "avg_likes_diff": round(ma.avg_likes - mb.avg_likes, 1),
            "avg_comments_diff": round(ma.avg_comments - mb.avg_comments, 1),
            "avg_shares_diff": round(ma.avg_shares - mb.avg_shares, 1),
            "viral_posts_diff": len(ma.viral_posts) - len(mb.viral_posts),
            "trend_a": ma.engagement_trend,
            "trend_b": mb.engagement_trend,
            "winner": "A" if ma.avg_engagement_rate > mb.avg_engagement_rate else "B",
        }

    def get_weaknesses(self, competitor_id: str) -> List[str]:
        """Identify engagement weaknesses."""
        metrics = self._metrics.get(competitor_id)
        if not metrics:
            return []

        weaknesses = []
        if metrics.avg_engagement_rate < 1.0:
            weaknesses.append("Very low engagement rate (< 1%)")
        if metrics.avg_comments < 1:
            weaknesses.append("Low comment count (audience not interacting)")
        if metrics.avg_shares < 0.5:
            weaknesses.append("Low shares (content not being spread)")
        if metrics.engagement_trend == "declining":
            weaknesses.append("Engagement is declining over time")
        if metrics.comment_to_like_ratio < 0.01:
            weaknesses.append("Almost no comments relative to likes (passive audience)")
        return weaknesses

    def get_strengths(self, competitor_id: str) -> List[str]:
        """Identify engagement strengths."""
        metrics = self._metrics.get(competitor_id)
        if not metrics:
            return []

        strengths = []
        if metrics.avg_engagement_rate >= 5.0:
            strengths.append("High engagement rate (>= 5%)")
        if metrics.avg_comments >= 10:
            strengths.append("Strong comment activity")
        if metrics.avg_shares >= 5:
            strengths.append("Good share rate (content spreading)")
        if metrics.engagement_trend == "growing":
            strengths.append("Engagement growing over time")
        if len(metrics.viral_posts) >= 3:
            strengths.append("Multiple viral posts")
        return strengths
