"""Signal Manager - Orchestrator for Learning Signals Module."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer03_intelligence.modules.learning_signals.signal_collector import SignalCollector
from layers.layer03_intelligence.modules.learning_signals.signal_normalizer import SignalNormalizer
from layers.layer03_intelligence.modules.learning_signals.engagement_calculator import EngagementCalculator
from layers.layer03_intelligence.modules.learning_signals.feedback_analyzer import FeedbackAnalyzer
from layers.layer03_intelligence.modules.learning_signals.performance_tracker import PerformanceTracker


class LearningSignalsResult:
    __slots__ = ("normalized_signals", "engagement", "feedback", "performance_trend",
                 "overall_learning_score", "recommendations", "timestamp")
    def __init__(self) -> None:
        self.normalized_signals: List[Dict] = []
        self.engagement: Optional[Any] = None
        self.feedback: Optional[Any] = None
        self.performance_trend = ""
        self.overall_learning_score = 0.0
        self.recommendations: List[str] = []
        self.timestamp = time.time()
    def to_dict(self) -> Dict:
        return {
            "normalized_signals": self.normalized_signals,
            "engagement": self.engagement.to_dict() if self.engagement else None,
            "feedback": self.feedback.to_dict() if self.feedback else None,
            "performance_trend": self.performance_trend,
            "overall_learning_score": round(self.overall_learning_score, 3),
            "recommendations": list(self.recommendations),
            "timestamp": self.timestamp,
        }


class SignalManager:
    def __init__(self) -> None:
        self.collector = SignalCollector()
        self.normalizer = SignalNormalizer()
        self.engagement = EngagementCalculator()
        self.feedback_analyzer = FeedbackAnalyzer()
        self.performance = PerformanceTracker()

    def analyze(self, data: Dict) -> LearningSignalsResult:
        result = LearningSignalsResult()

        # Collect and normalize signals
        raw_signals = data.get("signals", [])
        for sig in raw_signals:
            self.collector.add(sig.get("source", ""), sig.get("type", ""), sig.get("value", 0))
            norm = self.normalizer.normalize(sig.get("type", ""), sig.get("value", 0))
            result.normalized_signals.append(norm.to_dict())

        # Engagement
        metrics = data.get("metrics", {})
        reach = data.get("reach", 1)
        if metrics:
            result.engagement = self.engagement.calculate(metrics, reach)

        # Feedback
        comments = data.get("comments", [])
        if comments:
            result.feedback = self.feedback_analyzer.analyze(comments)

        # Performance trend
        post_id = data.get("post_id", "")
        if post_id and metrics:
            self.performance.record(post_id, metrics)
        result.performance_trend = self.performance.get_trend()

        # Overall learning score
        scores = []
        if result.engagement:
            scores.append(result.engagement.score)
        if result.feedback:
            scores.append(result.feedback.positive_ratio)
        avg_perf = self.performance.get_average_score()
        if avg_perf > 0:
            scores.append(avg_perf)
        result.overall_learning_score = sum(scores) / len(scores) if scores else 0.5

        # Recommendations
        if result.engagement and result.engagement.grade in ("D", "C"):
            result.recommendations.append("Improve content quality based on engagement data")
        if result.feedback and result.feedback.negative_ratio > 0.4:
            result.recommendations.append("Address negative feedback themes")
        if result.performance_trend == "declining":
            result.recommendations.append("Review and adjust content strategy")

        return result

    def get_health(self) -> Dict:
        return {
            "modules": ["SignalCollector", "SignalNormalizer", "EngagementCalculator",
                       "FeedbackAnalyzer", "PerformanceTracker"],
            "status": "healthy",
            "signals_collected": self.collector.count(),
            "performance_snapshots": self.performance.count(),
        }
