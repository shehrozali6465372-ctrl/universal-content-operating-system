"""Feedback Collector - Collects and aggregates feedback on recommendations."""
from __future__ import annotations
import time
from typing import Dict, List


class FeedbackItem:
    __slots__ = ("topic", "feedback_type", "value", "source", "timestamp")
    def __init__(self, topic: str = "", feedback_type: str = "", value: float = 0.0, source: str = ""):
        self.topic = topic
        self.feedback_type = feedback_type  # engagement, conversion, quality, relevance
        self.value = value
        self.source = source
        self.timestamp = time.time()
    def to_dict(self) -> Dict:
        return {"topic": self.topic, "type": self.feedback_type, "value": round(self.value, 3),
                "source": self.source, "timestamp": self.timestamp}


class FeedbackCollector:
    def __init__(self) -> None:
        self._feedback: List[FeedbackItem] = []

    def collect(self, feedback: FeedbackItem) -> None:
        self._feedback.append(feedback)

    def add(self, topic: str, feedback_type: str, value: float, source: str = "") -> None:
        self.collect(FeedbackItem(topic, feedback_type, value, source))

    def get_for_topic(self, topic: str) -> List[FeedbackItem]:
        return [f for f in self._feedback if f.topic.lower() == topic.lower()]

    def get_average(self, topic: str, feedback_type: str = "") -> float:
        items = self.get_for_topic(topic)
        if feedback_type:
            items = [f for f in items if f.feedback_type == feedback_type]
        if not items: return 0.0
        return sum(f.value for f in items) / len(items)

    def get_aggregate(self) -> Dict[str, float]:
        by_type: Dict[str, List[float]] = {}
        for f in self._feedback:
            by_type.setdefault(f.feedback_type, []).append(f.value)
        return {t: sum(v) / len(v) for t, v in by_type.items()}

    def count(self) -> int:
        return len(self._feedback)
