"""Decision Memory - Stores and retrieves past decisions."""
from __future__ import annotations
import time
from typing import Dict, List, Optional


class DecisionRecord:
    """A stored decision record."""
    __slots__ = ("decision_id", "context", "chosen_option", "alternatives",
                 "confidence", "outcome", "timestamp", "metadata")

    def __init__(self, decision_id: str = "", context: Optional[Dict] = None):
        self.decision_id = decision_id
        self.context = context or {}
        self.chosen_option = ""
        self.alternatives: List[str] = []
        self.confidence = 0.0
        self.outcome = "pending"  # pending, success, failure, partial
        self.timestamp = time.time()
        self.metadata: Dict = {}

    def to_dict(self) -> Dict:
        return {
            "decision_id": self.decision_id, "chosen_option": self.chosen_option,
            "alternatives": list(self.alternatives), "confidence": round(self.confidence, 3),
            "outcome": self.outcome, "timestamp": self.timestamp,
        }


class DecisionMemory:
    """Stores and retrieves past decisions for learning."""

    def __init__(self, max_records: int = 1000) -> None:
        self._records: List[DecisionRecord] = []
        self._max = max_records

    def store(self, record: DecisionRecord) -> None:
        self._records.append(record)
        if len(self._records) > self._max:
            self._records = self._records[-self._max:]

    def create_and_store(self, decision_id: str, chosen: str, confidence: float,
                         context: Optional[Dict] = None) -> DecisionRecord:
        record = DecisionRecord(decision_id, context)
        record.chosen_option = chosen
        record.confidence = confidence
        self.store(record)
        return record

    def get(self, decision_id: str) -> Optional[DecisionRecord]:
        for r in self._records:
            if r.decision_id == decision_id:
                return r
        return None

    def get_recent(self, n: int = 10) -> List[DecisionRecord]:
        return self._records[-n:]

    def get_successful(self) -> List[DecisionRecord]:
        return [r for r in self._records if r.outcome == "success"]

    def get_failed(self) -> List[DecisionRecord]:
        return [r for r in self._records if r.outcome == "failure"]

    def get_success_rate(self) -> float:
        outcomes = [r.outcome for r in self._records if r.outcome != "pending"]
        if not outcomes:
            return 0.0
        return sum(1 for o in outcomes if o == "success") / len(outcomes)

    def record_outcome(self, decision_id: str, outcome: str) -> bool:
        for r in self._records:
            if r.decision_id == decision_id:
                r.outcome = outcome
                return True
        return False

    def count(self) -> int:
        return len(self._records)

    def to_dict(self) -> Dict:
        return {"count": self.count(), "success_rate": round(self.get_success_rate(), 3),
                "records": [r.to_dict() for r in self._records[-20:]]}
