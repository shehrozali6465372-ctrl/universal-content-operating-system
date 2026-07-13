"""
Topic Scorer
Layer 2: Research Engine — Module 2

Multi-dimensional topic scoring for Facebook content strategy:
- Engagement potential scoring
- Audience fit analysis
- Competition level assessment
- Niche-specific weight adjustments
- Historical performance learning
"""

from typing import Dict, List, Optional
from layers.layer02_research.modules.topic_intelligence.topic_entry import TopicEntry


# Default niche-specific scoring weights
NICHE_WEIGHTS: Dict[str, Dict[str, float]] = {
    "finance": {"engagement": 0.3, "audience_fit": 0.3, "competition": 0.4},
    "technology": {"engagement": 0.35, "audience_fit": 0.3, "competition": 0.35},
    "health": {"engagement": 0.4, "audience_fit": 0.35, "competition": 0.25},
    "lifestyle": {"engagement": 0.45, "audience_fit": 0.35, "competition": 0.2},
    "education": {"engagement": 0.3, "audience_fit": 0.4, "competition": 0.3},
    "entertainment": {"engagement": 0.5, "audience_fit": 0.3, "competition": 0.2},
    "business": {"engagement": 0.3, "audience_fit": 0.35, "competition": 0.35},
    "marketing": {"engagement": 0.35, "audience_fit": 0.35, "competition": 0.3},
    "ai": {"engagement": 0.4, "audience_fit": 0.3, "competition": 0.3},
    "crypto": {"engagement": 0.5, "audience_fit": 0.25, "competition": 0.25},
    "fitness": {"engagement": 0.45, "audience_fit": 0.35, "competition": 0.2},
    "cooking": {"engagement": 0.4, "audience_fit": 0.4, "competition": 0.2},
    "travel": {"engagement": 0.45, "audience_fit": 0.35, "competition": 0.2},
    "parenting": {"engagement": 0.5, "audience_fit": 0.4, "competition": 0.1},
    "motivation": {"engagement": 0.5, "audience_fit": 0.35, "competition": 0.15},
    "general": {"engagement": 0.35, "audience_fit": 0.35, "competition": 0.3},
}

DEFAULT_WEIGHTS = NICHE_WEIGHTS["general"]


class TopicScorer:
    """Multi-dimensional scoring engine for Facebook topics."""

    def __init__(self):
        self._weights: Dict[str, Dict[str, float]] = dict(NICHE_WEIGHTS)
        self._history_scores: Dict[str, List[float]] = {}
        self._adjustment_factors: Dict[str, float] = {}

    def get_weights(self, niche: str) -> Dict[str, float]:
        return dict(self._weights.get(niche, DEFAULT_WEIGHTS))

    def set_weights(self, niche: str, weights: Dict[str, float]):
        """Override weights for a niche."""
        total = weights.get("engagement", 0) + weights.get("audience_fit", 0) + weights.get("competition", 0)
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        self._weights[niche] = dict(weights)

    def score_topic(
        self,
        topic: TopicEntry,
        niche_weights: Optional[Dict[str, float]] = None,
    ) -> TopicEntry:
        """Recalculate topic scores using niche-appropriate weights."""
        weights = niche_weights or self.get_weights(topic.niche)

        # Apply any adjustment factors
        adj = self._adjustment_factors.get(topic.niche, 1.0)

        # Recalculate opportunity
        raw_opportunity = (
            (topic.engagement_score * weights.get("engagement", 0.35)) +
            (topic.audience_fit_score * weights.get("audience_fit", 0.35)) +
            ((10.0 - topic.competition_score) * weights.get("competition", 0.3))
        )
        topic.opportunity_score = round(TopicEntry._clamp(raw_opportunity * adj), 2)

        # Recalculate composite
        topic.composite_score = round(
            (topic.engagement_score * 0.35 +
             topic.audience_fit_score * 0.25 +
             topic.opportunity_score * 0.25 +
             topic.confidence * 10.0 * 0.15),
            2,
        )
        return topic

    def batch_score(self, topics: List[TopicEntry]) -> List[TopicEntry]:
        """Score a batch of topics."""
        for topic in topics:
            self.score_topic(topic)
        return topics

    def rank_topics(self, topics: List[TopicEntry]) -> List[TopicEntry]:
        """Return topics sorted by composite score (highest first)."""
        return sorted(topics, key=lambda t: t.composite_score, reverse=True)

    def filter_by_threshold(
        self,
        topics: List[TopicEntry],
        min_composite: float = 5.0,
        min_engagement: float = 3.0,
        min_confidence: float = 0.3,
    ) -> List[TopicEntry]:
        """Filter topics by minimum thresholds."""
        return [
            t for t in topics
            if t.composite_score >= min_composite
            and t.engagement_score >= min_engagement
            and t.confidence >= min_confidence
        ]

    def record_performance(self, topic_id: str, score: float):
        """Record historical performance for learning."""
        if topic_id not in self._history_scores:
            self._history_scores[topic_id] = []
        self._history_scores[topic_id].append(max(0.0, min(10.0, score)))

    def get_average_performance(self, topic_id: str) -> Optional[float]:
        """Get average historical performance for a topic."""
        scores = self._history_scores.get(topic_id, [])
        if not scores:
            return None
        return round(sum(scores) / len(scores), 2)

    def set_adjustment_factor(self, niche: str, factor: float):
        """Set a global adjustment factor for a niche."""
        self._adjustment_factors[niche] = max(0.1, min(3.0, factor))

    def get_difficulty_label(self, topic: TopicEntry) -> str:
        """Return human-readable difficulty."""
        if topic.competition_score >= 8.0:
            return "very_hard"
        elif topic.competition_score >= 6.0:
            return "hard"
        elif topic.competition_score >= 3.0:
            return "medium"
        return "easy"

    def suggest_hashtags(self, topic: TopicEntry, max_count: int = 10) -> List[str]:
        """Suggest hashtags based on topic keywords and niche."""
        suggestions = []
        # From existing hashtags
        suggestions.extend(topic.hashtags)
        # From keywords
        for kw in topic.keywords[:max_count]:
            tag = f"#{kw.lower().replace(' ', '')}"
            if tag not in suggestions:
                suggestions.append(tag)
        # Niche tag
        niche_tag = f"#{topic.niche}"
        if niche_tag not in suggestions:
            suggestions.append(niche_tag)
        return suggestions[:max_count]
