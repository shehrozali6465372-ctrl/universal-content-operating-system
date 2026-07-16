"""Engagement Scorer — Estimate content engagement potential."""
from __future__ import annotations
from typing import Any, Dict, List


class EngagementScore:
    """Engagement potential score."""
    __slots__ = ("engagement_score", "hook_strength", "question_detected",
                 "emotional_words", "power_words", "urgency_score",
                 "shareability", "comment_probability", "issues")

    def __init__(self) -> None:
        self.engagement_score = 0.0
        self.hook_strength = 0.0
        self.question_detected = False
        self.emotional_words = 0
        self.power_words = 0
        self.urgency_score = 0.0
        self.shareability = 0.0
        self.comment_probability = 0.0
        self.issues: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engagement_score": round(self.engagement_score, 3),
            "hook_strength": round(self.hook_strength, 3),
            "question_detected": self.question_detected,
            "emotional_words": self.emotional_words,
            "power_words": self.power_words,
            "urgency_score": round(self.urgency_score, 3),
            "shareability": round(self.shareability, 3),
            "comment_probability": round(self.comment_probability, 3),
            "issues": self.issues,
        }


EMOTIONAL_WORDS = {"amazing", "incredible", "shocking", "unbelievable", "stunning", "powerful",
                   "transform", "revolutionary", "breakthrough", "discover", "secret", "proven",
                   "exclusive", "free", "instant", "now", "today", "urgent", "warning"}
POWER_WORDS = {"you", "your", "new", "free", "secret", "proven", "exclusive", "guaranteed",
               "essential", "critical", "must", "best", "top", "ultimate"}


class EngagementScorer:
    """Estimates content engagement potential."""

    def __init__(self) -> None:
        self._score_count = 0

    def score(self, text: str) -> EngagementScore:
        """Score content engagement potential."""
        result = EngagementScore()
        text_lower = text.lower()
        words = set(text_lower.split())

        # Questions
        result.question_detected = '?' in text

        # Emotional words
        result.emotional_words = sum(1 for w in words if w in EMOTIONAL_WORDS)

        # Power words
        result.power_words = sum(1 for w in words if w in POWER_WORDS)

        # Hook strength (first 50 chars)
        first_50 = text_lower[:50]
        hook_words = {"did you know", "what if", "here's", "discover", "secret", "proven"}
        result.hook_strength = 0.8 if any(h in first_50 for h in hook_words) else 0.4

        # Urgency
        urgency_words = {"now", "today", "limited", "hurry", "don't miss", "last chance", "urgent"}
        result.urgency_score = min(sum(1 for w in words if w in urgency_words) * 0.2, 1.0)

        # Shareability
        if result.emotional_words >= 2:
            result.shareability = 0.8
        elif result.emotional_words >= 1:
            result.shareability = 0.6
        else:
            result.shareability = 0.4

        # Comment probability
        if result.question_detected:
            result.comment_probability = 0.7
        elif result.power_words >= 2:
            result.comment_probability = 0.5
        else:
            result.comment_probability = 0.3

        # Overall
        weights = [0.2, 0.2, 0.2, 0.2, 0.2]
        scores = [result.hook_strength, result.shareability,
                  result.comment_probability, result.urgency_score,
                  min((result.emotional_words + result.power_words) * 0.1, 1.0)]
        result.engagement_score = round(sum(s * w for s, w in zip(scores, weights)), 3)

        if not result.question_detected:
            result.issues.append("No question — adding one can boost comments")

        self._score_count += 1
        return result

    @property
    def score_count(self) -> int:
        return self._score_count
