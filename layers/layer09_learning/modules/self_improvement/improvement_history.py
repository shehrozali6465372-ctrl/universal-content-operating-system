"""Improvement History — Track improvement history and milestones."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List, Optional

_IH_COUNTER = itertools.count(1)


class HistoryEntry:
    """A single improvement history entry."""

    __slots__ = ("entry_id", "event_type", "title", "description",
                 "score_before", "score_after", "timestamp", "tags")

    def __init__(self, event_type: str = "improvement") -> None:
        self.entry_id: str = f"ih_{next(_IH_COUNTER)}"
        self.event_type = event_type
        self.title: str = ""
        self.description: str = ""
        self.score_before: float = 0.0
        self.score_after: float = 0.0
        self.timestamp: float = time.time()
        self.tags: List[str] = []

    @property
    def improvement_delta(self) -> float:
        return round(self.score_after - self.score_before, 3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "event_type": self.event_type,
            "title": self.title,
            "score_before": round(self.score_before, 3),
            "score_after": round(self.score_after, 3),
            "improvement_delta": self.improvement_delta,
        }


class ImprovementHistory:
    """Track improvement history with milestones."""

    def __init__(self) -> None:
        self._entries: List[HistoryEntry] = []
        self._milestones: List[Dict[str, Any]] = []

    def record(self, event_type: str, title: str, description: str = "",
               score_before: float = 0.0, score_after: float = 0.0,
               tags: Optional[List[str]] = None) -> HistoryEntry:
        entry = HistoryEntry(event_type)
        entry.title = title
        entry.description = description
        entry.score_before = score_before
        entry.score_after = score_after
        if tags:
            entry.tags = list(tags)
        self._entries.append(entry)
        self._check_milestones(score_after)
        return entry

    def get_entries(self, event_type: str = "", limit: int = 0) -> List[HistoryEntry]:
        result = self._entries
        if event_type:
            result = [e for e in result if e.event_type == event_type]
        if limit > 0:
            return result[-limit:]
        return list(result)

    def get_improvements(self) -> List[HistoryEntry]:
        return [e for e in self._entries if e.improvement_delta > 0]

    def get_regressions(self) -> List[HistoryEntry]:
        return [e for e in self._entries if e.improvement_delta < 0]

    def get_milestones(self) -> List[Dict[str, Any]]:
        return list(self._milestones)

    def _check_milestones(self, score: float) -> None:
        thresholds = [0.5, 0.7, 0.8, 0.9, 0.95, 1.0]
        for t in thresholds:
            if score >= t and not any(m.get("threshold") == t for m in self._milestones):
                self._milestones.append({
                    "threshold": t,
                    "score": score,
                    "timestamp": time.time(),
                })

    @property
    def entry_count(self) -> int:
        return len(self._entries)
