"""
Shared Decision Models
Frozen interface — v1.0.0
"""

from datetime import datetime, timezone
from typing import List, Optional


class DecisionRecord:
    """A single decision made by the agent."""

    __slots__ = (
        "decision_id", "question", "answer", "confidence",
        "reasoning", "data_sources", "module", "topic",
        "created_at",
    )

    def __init__(
        self,
        question: str,
        answer: str = "",
        confidence: float = 0.0,
        reasoning: str = "",
        data_sources: Optional[List[str]] = None,
        module: str = "",
        topic: str = "",
    ):
        self.decision_id = f"dec_{hash(question) % 1000000}"
        self.question = question
        self.answer = answer
        self.confidence = max(0.0, min(1.0, confidence))
        self.reasoning = reasoning
        self.data_sources = data_sources or []
        self.module = module
        self.topic = topic
        self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "question": self.question,
            "answer": self.answer,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "data_sources": list(self.data_sources),
            "module": self.module,
            "topic": self.topic,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DecisionRecord":
        d = cls(
            question=data.get("question", ""),
            answer=data.get("answer", ""),
            confidence=data.get("confidence", 0.0),
            reasoning=data.get("reasoning", ""),
            data_sources=data.get("data_sources", []),
            module=data.get("module", ""),
            topic=data.get("topic", ""),
        )
        d.decision_id = data.get("decision_id", d.decision_id)
        d.created_at = data.get("created_at", d.created_at)
        return d

    def __repr__(self) -> str:
        return f"DecisionRecord(question='{self.question[:50]}', confidence={self.confidence})"


class DecisionTrace:
    """Full trace of decisions made during a research/execution cycle."""

    __slots__ = ("trace_id", "topic", "records", "overall_confidence", "created_at")

    def __init__(self, topic: str = ""):
        self.trace_id = f"trace_{int(datetime.now(timezone.utc).timestamp())}_{hash(topic) % 100000}"
        self.topic = topic
        self.records: List[DecisionRecord] = []
        self.overall_confidence = 0.0
        self.created_at = datetime.now(timezone.utc).isoformat()

    def add(self, record: DecisionRecord):
        self.records.append(record)
        self._recalculate()

    def get_by_module(self, module: str) -> List[DecisionRecord]:
        return [r for r in self.records if r.module == module]

    def get_by_topic(self, topic: str) -> List[DecisionRecord]:
        return [r for r in self.records if r.topic == topic]

    def get_lowest_confidence(self) -> Optional[DecisionRecord]:
        if not self.records:
            return None
        return min(self.records, key=lambda r: r.confidence)

    def get_highest_confidence(self) -> Optional[DecisionRecord]:
        if not self.records:
            return None
        return max(self.records, key=lambda r: r.confidence)

    def count(self) -> int:
        return len(self.records)

    def _recalculate(self):
        if not self.records:
            self.overall_confidence = 0.0
            return
        self.overall_confidence = round(
            sum(r.confidence for r in self.records) / len(self.records), 3
        )

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "topic": self.topic,
            "records": [r.to_dict() for r in self.records],
            "overall_confidence": self.overall_confidence,
            "count": self.count(),
            "created_at": self.created_at,
        }

    def __repr__(self) -> str:
        return f"DecisionTrace(topic='{self.topic}', decisions={self.count()})"
