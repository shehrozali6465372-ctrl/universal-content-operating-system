"""Conflict Resolver — Resolve AI disagreements."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_CR_COUNTER = itertools.count(1)


class Conflict:
    """A conflict between AI suggestions."""

    __slots__ = ("conflict_id", "source_a", "suggestion_a", "source_b",
                 "suggestion_b", "resolution", "timestamp", "resolved")

    def __init__(self, source_a: str = "", suggestion_a: str = "",
                 source_b: str = "", suggestion_b: str = "") -> None:
        self.conflict_id: str = f"conf_{next(_CR_COUNTER)}"
        self.source_a = source_a
        self.suggestion_a = suggestion_a
        self.source_b = source_b
        self.suggestion_b = suggestion_b
        self.resolution: str = ""
        self.timestamp: float = time.time()
        self.resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id, "resolution": self.resolution,
            "resolved": self.resolved,
        }


class ConflictResolver:
    """Resolve conflicts between AI engine suggestions."""

    RESOLUTION_STRATEGIES = ("priority", "confidence", "consensus", "compromise", "human_review")

    def __init__(self) -> None:
        self._conflicts: List[Conflict] = []
        self._resolution_history: List[Dict[str, Any]] = []

    def detect_conflict(self, suggestions: Dict[str, str]) -> Optional[Conflict]:
        unique = set(suggestions.values())
        if len(unique) <= 1:
            return None
        items = list(suggestions.items())
        conflict = Conflict(items[0][0], items[0][1], items[1][0], items[1][1])
        self._conflicts.append(conflict)
        return conflict

    def resolve(self, conflict_id: str, strategy: str = "priority",
                context: Optional[Dict[str, Any]] = None) -> Optional[Conflict]:
        for c in self._conflicts:
            if c.conflict_id == conflict_id:
                if strategy == "priority":
                    c.resolution = c.source_a
                elif strategy == "consensus":
                    c.resolution = "compromise"
                elif strategy == "human_review":
                    c.resolution = "pending_human_review"
                else:
                    c.resolution = c.source_a
                c.resolved = True
                self._resolution_history.append({
                    "conflict_id": conflict_id, "strategy": strategy,
                    "resolution": c.resolution, "time": time.time(),
                })
                return c
        return None

    def get_unresolved(self) -> List[Conflict]:
        return [c for c in self._conflicts if not c.resolved]

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._resolution_history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total": len(self._conflicts),
            "resolved": sum(1 for c in self._conflicts if c.resolved),
            "unresolved": sum(1 for c in self._conflicts if not c.resolved),
        }
