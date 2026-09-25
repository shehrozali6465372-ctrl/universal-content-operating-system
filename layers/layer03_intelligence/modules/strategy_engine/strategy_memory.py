"""Bounded, thread-safe strategy memory with stable record identifiers."""
from __future__ import annotations
import copy
import math
from threading import RLock
from typing import Any, Dict, List, Optional
from uuid import uuid4


class StrategyRecord:
    """A stored strategy record with outcome."""
    __slots__ = ("record_id", "strategy_id", "strategy_data", "outcome",
                 "performance_score", "lessons", "timestamp", "tags")

    def __init__(self, strategy_id: str = "", strategy_data: Optional[Dict] = None) -> None:
        self.record_id = f"rec_{uuid4().hex}"
        self.strategy_id = strategy_id
        self.strategy_data = copy.deepcopy(strategy_data or {})
        self.outcome = "unknown"
        self.performance_score = 0.0
        self.lessons: List[str] = []
        self.timestamp = __import__("time").time()
        self.tags: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "strategy_id": self.strategy_id,
            "outcome": self.outcome,
            "performance_score": round(self.performance_score, 3),
            "lessons": list(self.lessons),
            "tags": list(self.tags),
            "timestamp": self.timestamp,
        }


class StrategyMemory:
    """Stores past strategies with bounded retention and isolated reads."""

    def __init__(self, max_size: int = 500) -> None:
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        self._records: List[StrategyRecord] = []
        self._max_size = max_size
        self._index: Dict[str, List[str]] = {}
        self._lock = RLock()

    @staticmethod
    def _snapshot(record: StrategyRecord) -> StrategyRecord:
        return copy.deepcopy(record)

    def _rebuild_index(self) -> None:
        self._index.clear()
        for record in self._records:
            if record.strategy_id:
                self._index.setdefault(record.strategy_id, []).append(record.record_id)

    def store(
        self,
        strategy_data: Dict[str, Any],
        outcome: str = "unknown",
        performance_score: float = 0.0,
        lessons: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> StrategyRecord:
        """Store a strategy with its outcome."""
        if not math.isfinite(performance_score):
            raise ValueError("performance_score must be finite")
        rec = StrategyRecord(
            strategy_id=strategy_data.get("strategy_id", ""),
            strategy_data=strategy_data,
        )
        rec.outcome = outcome
        rec.performance_score = performance_score
        rec.lessons = list(lessons or [])
        rec.tags = list(tags or [])

        with self._lock:
            if len(self._records) >= self._max_size:
                self._records.pop(0)
                self._rebuild_index()
            self._records.append(rec)
            if rec.strategy_id:
                self._index.setdefault(rec.strategy_id, []).append(rec.record_id)
            return self._snapshot(rec)

    def get(self, record_id: str) -> Optional[StrategyRecord]:
        with self._lock:
            for record in self._records:
                if record.record_id == record_id:
                    return self._snapshot(record)
        return None

    def get_by_strategy(self, strategy_id: str) -> List[StrategyRecord]:
        with self._lock:
            return [
                self._snapshot(record)
                for record in self._records
                if record.strategy_id == strategy_id
            ]

    def get_successful(self, min_score: float = 0.7) -> List[StrategyRecord]:
        with self._lock:
            return [
                self._snapshot(record)
                for record in self._records
                if record.outcome == "success" and record.performance_score >= min_score
            ]

    def get_failed(self) -> List[StrategyRecord]:
        with self._lock:
            return [self._snapshot(record) for record in self._records if record.outcome == "failure"]

    def get_similar(self, tags: List[str], limit: int = 5) -> List[StrategyRecord]:
        if limit < 0:
            raise ValueError("limit must be >= 0")
        tag_set = set(tags)
        with self._lock:
            scored = []
            for record in self._records:
                overlap = len(tag_set & set(record.tags))
                if overlap > 0:
                    scored.append((overlap, record))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [self._snapshot(record) for _, record in scored[:limit]]

    def get_lessons(self, topic: str = "") -> List[str]:
        with self._lock:
            lessons: List[str] = []
            for record in self._records:
                if record.outcome == "failure" and record.lessons:
                    lessons.extend(record.lessons)
                if topic and topic.lower() in str(record.strategy_data).lower():
                    lessons.extend(record.lessons)
            return list(dict.fromkeys(lessons))

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._records)
            if total == 0:
                return {"total": 0, "success_rate": 0.0}
            success = sum(1 for record in self._records if record.outcome == "success")
            failure = sum(1 for record in self._records if record.outcome == "failure")
            avg_score = sum(record.performance_score for record in self._records) / total
            return {
                "total": total,
                "success": success,
                "failure": failure,
                "success_rate": round(success / total, 3),
                "avg_performance": round(avg_score, 3),
            }

    def clear(self) -> None:
        with self._lock:
            self._records.clear()
            self._index.clear()

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._records)
