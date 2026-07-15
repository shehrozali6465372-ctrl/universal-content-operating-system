"""Recommendation Memory - Stores past recommendations and their outcomes."""
from __future__ import annotations
import time
from typing import Dict, List


class RecRecord:
    __slots__ = ("topic", "score", "confidence", "outcome", "timestamp", "metadata")
    def __init__(self, topic: str = "", score: float = 0.0, confidence: float = 0.0):
        self.topic = topic
        self.score = score
        self.confidence = confidence
        self.outcome = "pending"
        self.timestamp = time.time()
        self.metadata: Dict = {}
    def to_dict(self) -> Dict:
        return {"topic": self.topic, "score": round(self.score, 3), "confidence": round(self.confidence, 3),
                "outcome": self.outcome, "timestamp": self.timestamp}


class RecommendationMemory:
    def __init__(self, max_records: int = 500) -> None:
        self._records: List[RecRecord] = []
        self._max = max_records

    def store(self, record: RecRecord) -> None:
        self._records.append(record)
        if len(self._records) > self._max:
            self._records = self._records[-self._max:]

    def record_outcome(self, topic: str, outcome: str) -> bool:
        for r in reversed(self._records):
            if r.topic == topic:
                r.outcome = outcome
                return True
        return False

    def get_successful(self) -> List[RecRecord]:
        return [r for r in self._records if r.outcome == "success"]

    def get_failed(self) -> List[RecRecord]:
        return [r for r in self._records if r.outcome == "failure"]

    def get_success_rate(self) -> float:
        done = [r for r in self._records if r.outcome != "pending"]
        if not done: return 0.0
        return sum(1 for r in done if r.outcome == "success") / len(done)

    def was_recommended(self, topic: str) -> bool:
        return any(r.topic.lower() == topic.lower() for r in self._records)

    def count(self) -> int:
        return len(self._records)

    def to_dict(self) -> Dict:
        return {"count": self.count(), "success_rate": round(self.get_success_rate(), 3),
                "records": [r.to_dict() for r in self._records[-20:]]}
