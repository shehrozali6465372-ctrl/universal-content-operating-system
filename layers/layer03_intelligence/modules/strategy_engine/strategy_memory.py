"""Strategy Memory — Store and retrieve past strategies with outcomes."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class StrategyRecord:
    """A stored strategy record with outcome."""
    __slots__ = ("record_id", "strategy_id", "strategy_data", "outcome",
                 "performance_score", "lessons", "timestamp", "tags")

    def __init__(self, strategy_id: str = "", strategy_data: Optional[Dict] = None) -> None:
        self.record_id = f"rec_{int(time.time()*1000) % 10000000}"
        self.strategy_id = strategy_id
        self.strategy_data = strategy_data or {}
        self.outcome = "unknown"
        self.performance_score = 0.0
        self.lessons: List[str] = []
        self.timestamp = time.time()
        self.tags: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "strategy_id": self.strategy_id,
            "outcome": self.outcome,
            "performance_score": round(self.performance_score, 3),
            "lessons": self.lessons,
            "tags": self.tags,
            "timestamp": self.timestamp,
        }


class StrategyMemory:
    """Stores past strategies with outcomes for future reference."""

    def __init__(self, max_size: int = 500) -> None:
        self._records: List[StrategyRecord] = []
        self._max_size = max_size
        self._index: Dict[str, List[int]] = {}  # strategy_id -> indices

    def store(
        self,
        strategy_data: Dict[str, Any],
        outcome: str = "unknown",
        performance_score: float = 0.0,
        lessons: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> StrategyRecord:
        """Store a strategy with its outcome."""
        rec = StrategyRecord(
            strategy_id=strategy_data.get("strategy_id", ""),
            strategy_data=strategy_data,
        )
        rec.outcome = outcome
        rec.performance_score = performance_score
        rec.lessons = lessons or []
        rec.tags = tags or []

        if len(self._records) >= self._max_size:
            self._records.pop(0)

        idx = len(self._records)
        self._records.append(rec)

        sid = rec.strategy_id
        if sid:
            self._index.setdefault(sid, []).append(idx)

        return rec

    def get(self, record_id: str) -> Optional[StrategyRecord]:
        for r in self._records:
            if r.record_id == record_id:
                return r
        return None

    def get_by_strategy(self, strategy_id: str) -> List[StrategyRecord]:
        indices = self._index.get(strategy_id, [])
        return [self._records[i] for i in indices if i < len(self._records)]

    def get_successful(self, min_score: float = 0.7) -> List[StrategyRecord]:
        return [r for r in self._records if r.outcome == "success" and r.performance_score >= min_score]

    def get_failed(self) -> List[StrategyRecord]:
        return [r for r in self._records if r.outcome == "failure"]

    def get_similar(self, tags: List[str], limit: int = 5) -> List[StrategyRecord]:
        tag_set = set(tags)
        scored = []
        for r in self._records:
            overlap = len(tag_set & set(r.tags))
            if overlap > 0:
                scored.append((overlap, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored[:limit]]

    def get_lessons(self, topic: str = "") -> List[str]:
        lessons: List[str] = []
        for r in self._records:
            if r.outcome == "failure" and r.lessons:
                lessons.extend(r.lessons)
            if topic and topic.lower() in str(r.strategy_data).lower():
                lessons.extend(r.lessons)
        return list(dict.fromkeys(lessons))  # dedup preserving order

    def stats(self) -> Dict[str, Any]:
        total = len(self._records)
        if total == 0:
            return {"total": 0, "success_rate": 0.0}
        success = sum(1 for r in self._records if r.outcome == "success")
        failure = sum(1 for r in self._records if r.outcome == "failure")
        avg_score = sum(r.performance_score for r in self._records) / total
        return {
            "total": total,
            "success": success,
            "failure": failure,
            "success_rate": round(success / total, 3),
            "avg_performance": round(avg_score, 3),
        }

    def clear(self) -> None:
        self._records.clear()
        self._index.clear()

    @property
    def size(self) -> int:
        return len(self._records)
