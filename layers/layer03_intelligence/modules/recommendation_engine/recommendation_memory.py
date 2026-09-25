"""Recommendation Memory - Stores past recommendations and their outcomes."""
from __future__ import annotations
import time
import copy
from threading import RLock
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
        if max_records < 1:
            raise ValueError("max_records must be >= 1")
        self._records: List[RecRecord] = []
        self._max = max_records
        self._lock = RLock()

    def store(self, record: RecRecord) -> None:
        with self._lock:
            self._records.append(copy.deepcopy(record))
            if len(self._records) > self._max:
                self._records = self._records[-self._max:]

    def record_outcome(self, topic: str, outcome: str) -> bool:
        with self._lock:
            for r in reversed(self._records):
                if r.topic == topic:
                    r.outcome = outcome
                    return True
        return False

    def get_successful(self) -> List[RecRecord]:
        with self._lock:
            return copy.deepcopy([r for r in self._records if r.outcome == "success"])

    def get_failed(self) -> List[RecRecord]:
        with self._lock:
            return copy.deepcopy([r for r in self._records if r.outcome == "failure"])

    def get_success_rate(self) -> float:
        with self._lock:
            done = [r for r in self._records if r.outcome != "pending"]
        if not done: return 0.0
        return sum(1 for r in done if r.outcome == "success") / len(done)

    def was_recommended(self, topic: str) -> bool:
        with self._lock:
            return any(r.topic.lower() == topic.lower() for r in self._records)

    def count(self) -> int:
        with self._lock:
            return len(self._records)

    def to_dict(self) -> Dict:
        with self._lock:
            return {"count": len(self._records), "success_rate": round(self.get_success_rate(), 3),
                    "records": [r.to_dict() for r in self._records[-20:]]}
