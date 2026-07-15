"""Feedback Analyzer - Analyzes positive and negative feedback patterns."""
from __future__ import annotations
from typing import Dict, List


class FeedbackAnalysis:
    __slots__ = ("positive_ratio", "negative_ratio", "sentiment_trend", "top_positive", "top_negative")
    def __init__(self) -> None:
        self.positive_ratio = 0.0
        self.negative_ratio = 0.0
        self.sentiment_trend = "stable"
        self.top_positive: List[str] = []
        self.top_negative: List[str] = []
    def to_dict(self) -> Dict:
        return {"positive_ratio": round(self.positive_ratio, 3), "negative_ratio": round(self.negative_ratio, 3),
                "sentiment_trend": self.sentiment_trend, "top_positive": self.top_positive, "top_negative": self.top_negative}


class FeedbackAnalyzer:
    POSITIVE = {"love", "great", "amazing", "helpful", "thanks", "good", "best", "excellent", "useful", "awesome"}
    NEGATIVE = {"hate", "bad", "terrible", "worst", "spam", "boring", "wrong", "fake", "annoying", "stupid"}

    def analyze(self, comments: List[str]) -> FeedbackAnalysis:
        result = FeedbackAnalysis()
        if not comments:
            return result

        pos_count = 0
        neg_count = 0
        pos_words = []
        neg_words = []

        for comment in comments:
            words = set(w.lower().strip(".,!?") for w in comment.split())
            p = len(words & self.POSITIVE)
            n = len(words & self.NEGATIVE)
            pos_count += p
            neg_count += n
            pos_words.extend(words & self.POSITIVE)
            neg_words.extend(words & self.NEGATIVE)

        total = pos_count + neg_count
        if total > 0:
            result.positive_ratio = pos_count / total
            result.negative_ratio = neg_count / total

        if result.positive_ratio > 0.6: result.sentiment_trend = "improving"
        elif result.negative_ratio > 0.6: result.sentiment_trend = "declining"
        else: result.sentiment_trend = "stable"

        # Top words
        from collections import Counter
        pos_c = Counter(pos_words).most_common(5)
        neg_c = Counter(neg_words).most_common(5)
        result.top_positive = [w for w, _ in pos_c]
        result.top_negative = [w for w, _ in neg_c]
        return result
