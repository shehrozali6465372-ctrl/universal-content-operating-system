"""Case Retriever — Retrieve similar past cases by various criteria."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional


class Case:
    """A stored intelligence case."""
    __slots__ = ("case_id", "topic", "decision", "outcome", "score",
                 "tags", "metadata", "created_at", "relevance_score")

    def __init__(self, topic: str = "", decision: str = "") -> None:
        self.case_id = f"case_{next(_CASE_COUNTER)}"
        self.topic = topic
        self.decision = decision
        self.outcome = "unknown"
        self.score = 0.0
        self.tags: List[str] = []
        self.metadata: Dict[str, Any] = {}
        self.created_at = time.time()
        self.relevance_score = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "topic": self.topic,
            "decision": self.decision,
            "outcome": self.outcome,
            "score": round(self.score, 3),
            "tags": self.tags,
        }


_CASE_COUNTER = itertools.count(1)


class CaseRetriever:
    """Retrieves similar cases from case history."""

    def __init__(self) -> None:
        self._cases: List[Case] = []
        self._topic_index: Dict[str, List[int]] = {}
        self._tag_index: Dict[str, List[int]] = {}

    def store(self, topic: str, decision: str, outcome: str = "unknown",
              score: float = 0.0, tags: Optional[List[str]] = None,
              metadata: Optional[Dict] = None) -> Case:
        """Store a new case."""
        case = Case(topic=topic, decision=decision)
        case.outcome = outcome
        case.score = score
        case.tags = tags or []
        case.metadata = metadata or {}
        idx = len(self._cases)
        self._cases.append(case)
        self._topic_index.setdefault(topic.lower(), []).append(idx)
        for tag in case.tags:
            self._tag_index.setdefault(tag.lower(), []).append(idx)
        return case

    def get_similar(self, topic: str, limit: int = 5) -> List[Case]:
        """Find cases with similar topic."""
        idxs = self._topic_index.get(topic.lower(), [])
        cases = [self._cases[i] for i in idxs if i < len(self._cases)]
        return sorted(cases, key=lambda c: c.score, reverse=True)[:limit]

    def get_by_tag(self, tag: str, limit: int = 10) -> List[Case]:
        """Find cases by tag."""
        idxs = self._tag_index.get(tag.lower(), [])
        return [self._cases[i] for i in idxs if i < len(self._cases)][:limit]

    def get_successful(self, min_score: float = 0.7, limit: int = 10) -> List[Case]:
        """Get successful cases."""
        success = [c for c in self._cases if c.outcome == "success" and c.score >= min_score]
        return sorted(success, key=lambda c: c.score, reverse=True)[:limit]

    def get_failed(self, limit: int = 10) -> List[Case]:
        """Get failed cases."""
        failed = [c for c in self._cases if c.outcome == "failure"]
        return failed[:limit]

    def get_by_score_range(self, min_score: float, max_score: float) -> List[Case]:
        return [c for c in self._cases if min_score <= c.score <= max_score]

    def search(self, query: str, limit: int = 5) -> List[Case]:
        """Simple text search across topics and decisions."""
        query_lower = query.lower()
        results: List[Case] = []
        for c in self._cases:
            if query_lower in c.topic.lower() or query_lower in c.decision.lower():
                results.append(c)
        return results[:limit]

    @property
    def count(self) -> int:
        return len(self._cases)

    def clear(self) -> None:
        self._cases.clear()
        self._topic_index.clear()
        self._tag_index.clear()
