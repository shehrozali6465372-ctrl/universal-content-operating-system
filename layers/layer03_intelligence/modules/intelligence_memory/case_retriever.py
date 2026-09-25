"""Case Retriever — Retrieve similar past cases by various criteria."""
from __future__ import annotations
import itertools
import time
import copy
from threading import RLock
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
        self._lock = RLock()

    def store(self, topic: str, decision: str, outcome: str = "unknown",
              score: float = 0.0, tags: Optional[List[str]] = None,
              metadata: Optional[Dict] = None) -> Case:
        if not topic.strip():
            raise ValueError("topic must not be empty")
        if not isinstance(score, (int, float)):
            raise TypeError("score must be numeric")
        if not 0.0 <= score <= 1.0:
            raise ValueError("score must be between 0 and 1")
        case = Case(topic=topic, decision=decision)
        case.outcome = outcome
        case.score = score
        case.tags = list(tags or [])
        case.metadata = copy.deepcopy(metadata or {})
        with self._lock:
            idx = len(self._cases)
            self._cases.append(case)
            self._topic_index.setdefault(topic.lower(), []).append(idx)
            for tag in case.tags:
                self._tag_index.setdefault(tag.lower(), []).append(idx)
            return copy.deepcopy(case)

    def get_similar(self, topic: str, limit: int = 5) -> List[Case]:
        if limit < 0:
            raise ValueError("limit must be non-negative")
        with self._lock:
            idxs = self._topic_index.get(topic.lower(), [])
            return copy.deepcopy(sorted([self._cases[i] for i in idxs if i < len(self._cases)], key=lambda x: x.score, reverse=True)[:limit])

    def get_by_tag(self, tag: str, limit: int = 10) -> List[Case]:
        if limit < 0:
            raise ValueError("limit must be non-negative")
        with self._lock:
            idxs = self._tag_index.get(tag.lower(), [])
            return copy.deepcopy([self._cases[i] for i in idxs if i < len(self._cases)][:limit])

    def get_successful(self, min_score: float = 0.7, limit: int = 10) -> List[Case]:
        if not 0.0 <= min_score <= 1.0:
            raise ValueError("min_score must be between 0 and 1")
        if limit < 0:
            raise ValueError("limit must be non-negative")
        with self._lock:
            items = [x for x in self._cases if x.outcome == "success" and x.score >= min_score]
            return copy.deepcopy(sorted(items, key=lambda x: x.score, reverse=True)[:limit])

    def get_failed(self, limit: int = 10) -> List[Case]:
        if limit < 0:
            raise ValueError("limit must be non-negative")
        with self._lock:
            return copy.deepcopy([x for x in self._cases if x.outcome == "failure"][:limit])

    def get_by_score_range(self, min_score: float, max_score: float) -> List[Case]:
        if not 0.0 <= min_score <= max_score <= 1.0:
            raise ValueError("invalid score range")
        with self._lock:
            return copy.deepcopy([x for x in self._cases if min_score <= x.score <= max_score])

    def search(self, query: str, limit: int = 5) -> List[Case]:
        if limit < 0:
            raise ValueError("limit must be non-negative")
        q = query.lower()
        with self._lock:
            return copy.deepcopy([x for x in self._cases if q in x.topic.lower() or q in x.decision.lower()][:limit])

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._cases)

    def clear(self) -> None:
        with self._lock:
            self._cases.clear()
            self._topic_index.clear()
            self._tag_index.clear()
