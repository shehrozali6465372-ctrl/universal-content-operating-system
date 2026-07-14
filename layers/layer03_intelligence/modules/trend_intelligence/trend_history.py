"""Trend History - Stores snapshots of trend data over time."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class TrendSnapshot:
    """A single point-in-time snapshot of a trend."""
    __slots__ = ("topic", "timestamp", "score", "momentum", "lifecycle_stage",
                 "virality_score", "platform_count", "confidence", "metadata")

    def __init__(self, topic: str = "", timestamp: float = 0.0) -> None:
        self.topic = topic
        self.timestamp = timestamp or time.time()
        self.score = 0.0
        self.momentum = 0.0
        self.lifecycle_stage = "unknown"
        self.virality_score = 0.0
        self.platform_count = 0
        self.confidence = 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict:
        return {
            "topic": self.topic, "timestamp": self.timestamp,
            "score": round(self.score, 3), "momentum": round(self.momentum, 3),
            "lifecycle_stage": self.lifecycle_stage,
            "virality_score": round(self.virality_score, 3),
            "platform_count": self.platform_count,
            "confidence": round(self.confidence, 3),
            "metadata": dict(self.metadata),
        }


class TopicHistory:
    """History of snapshots for a single topic."""
    __slots__ = ("topic", "snapshots", "peak_score", "peak_timestamp",
                 "first_seen", "last_updated")

    def __init__(self, topic: str = "") -> None:
        self.topic = topic
        self.snapshots: List[TrendSnapshot] = []
        self.peak_score = 0.0
        self.peak_timestamp = 0.0
        self.first_seen = 0.0
        self.last_updated = 0.0

    def add_snapshot(self, snapshot: TrendSnapshot) -> None:
        self.snapshots.append(snapshot)
        if not self.first_seen:
            self.first_seen = snapshot.timestamp
        self.last_updated = snapshot.timestamp

        if snapshot.score > self.peak_score:
            self.peak_score = snapshot.score
            self.peak_timestamp = snapshot.timestamp

    def get_score_history(self) -> List[float]:
        return [s.score for s in self.snapshots]

    def get_momentum_history(self) -> List[float]:
        return [s.momentum for s in self.snapshots]

    def get_latest(self) -> Optional[TrendSnapshot]:
        return self.snapshots[-1] if self.snapshots else None

    def get_recent(self, n: int = 5) -> List[TrendSnapshot]:
        return self.snapshots[-n:]

    def days_tracked(self) -> float:
        if len(self.snapshots) < 2:
            return 0.0
        return (self.last_updated - self.first_seen) / 86400.0

    def to_dict(self) -> Dict:
        return {
            "topic": self.topic,
            "snapshot_count": len(self.snapshots),
            "peak_score": round(self.peak_score, 3),
            "first_seen": self.first_seen,
            "last_updated": self.last_updated,
            "days_tracked": round(self.days_tracked(), 1),
            "snapshots": [s.to_dict() for s in self.snapshots[-10:]],  # last 10 only
        }


class TrendHistory:
    """Stores historical snapshots of all tracked trends."""

    def __init__(self, max_snapshots_per_topic: int = 100) -> None:
        self._topics: Dict[str, TopicHistory] = {}
        self._max = max_snapshots_per_topic

    def record(self, topic: str, score: float = 0.0, momentum: float = 0.0,
               lifecycle_stage: str = "unknown", virality_score: float = 0.0,
               platform_count: int = 0, confidence: float = 0.0,
               metadata: Optional[Dict] = None) -> TrendSnapshot:
        snapshot = TrendSnapshot(topic)
        snapshot.score = score
        snapshot.momentum = momentum
        snapshot.lifecycle_stage = lifecycle_stage
        snapshot.virality_score = virality_score
        snapshot.platform_count = platform_count
        snapshot.confidence = confidence
        snapshot.metadata = metadata or {}

        if topic not in self._topics:
            self._topics[topic] = TopicHistory(topic)

        history = self._topics[topic]
        history.add_snapshot(snapshot)

        # Trim old snapshots
        if len(history.snapshots) > self._max:
            history.snapshots = history.snapshots[-self._max:]

        return snapshot

    def record_analysis(self, topic: str, analysis_result: Any) -> TrendSnapshot:
        """Record from a TrendAnalysisResult object."""
        score = 0.0
        momentum = 0.0
        lifecycle_stage = "unknown"
        virality_score = 0.0
        platform_count = 0
        confidence = 0.0

        if analysis_result.normalized:
            score = analysis_result.normalized.normalized_score
        if analysis_result.momentum:
            momentum = analysis_result.momentum.momentum_score
        if analysis_result.lifecycle:
            lifecycle_stage = analysis_result.lifecycle.stage
        if analysis_result.virality:
            virality_score = analysis_result.virality.virality_score
        if analysis_result.cross_platform:
            platform_count = analysis_result.cross_platform.platform_count
        if analysis_result.confidence:
            confidence = analysis_result.confidence.overall_confidence

        return self.record(topic, score, momentum, lifecycle_stage,
                          virality_score, platform_count, confidence)

    def get_topic_history(self, topic: str) -> Optional[TopicHistory]:
        return self._topics.get(topic)

    def get_all_topics(self) -> List[str]:
        return list(self._topics.keys())

    def get_score_history(self, topic: str) -> List[float]:
        h = self._topics.get(topic)
        return h.get_score_history() if h else []

    def get_trending_topics(self, min_score: float = 0.5) -> List[str]:
        result = []
        for topic, history in self._topics.items():
            latest = history.get_latest()
            if latest and latest.score >= min_score:
                result.append(topic)
        return result

    def get_declining_topics(self) -> List[str]:
        result = []
        for topic, history in self._topics.items():
            if history.lifecycle_stage == "declining" or len(history.snapshots) > 2:
                scores = history.get_score_history()
                if len(scores) >= 3 and scores[-1] < scores[-3] * 0.8:
                    result.append(topic)
        return result

    def get_stats(self) -> Dict:
        return {
            "total_topics": len(self._topics),
            "total_snapshots": sum(len(h.snapshots) for h in self._topics.values()),
            "topics": list(self._topics.keys()),
        }

    def to_dict(self) -> Dict:
        return {
            "stats": self.get_stats(),
            "topics": {t: h.to_dict() for t, h in self._topics.items()},
        }
