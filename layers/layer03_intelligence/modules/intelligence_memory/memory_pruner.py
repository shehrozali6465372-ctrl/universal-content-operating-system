"""Memory Pruner — Remove old, low-value, or stale memories."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class PruningResult:
    """Result of a pruning operation."""
    __slots__ = ("removed_count", "kept_count", "removed_ids", "pruning_reasons")

    def __init__(self) -> None:
        self.removed_count = 0
        self.kept_count = 0
        self.removed_ids: List[str] = []
        self.pruning_reasons: Dict[str, int] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "removed": self.removed_count,
            "kept": self.kept_count,
            "reasons": self.pruning_reasons,
        }


class MemoryPruner:
    """Prunes memories based on age, value, and staleness."""

    def __init__(self, max_age_days: int = 90, min_value: float = 0.1) -> None:
        self._max_age_seconds = max_age_days * 86400
        self._min_value = min_value

    def prune(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prune entries and return surviving ones."""
        result: List[Dict[str, Any]] = []
        now = time.time()
        for e in entries:
            age = now - e.get("timestamp", now)
            value = e.get("value", 0.5)
            if age > self._max_age_seconds:
                continue
            if value < self._min_value:
                continue
            result.append(e)
        return result

    def analyze(self, entries: List[Dict[str, Any]]) -> PruningResult:
        """Analyze what would be pruned without removing."""
        pr = PruningResult()
        now = time.time()
        for e in entries:
            age = now - e.get("timestamp", now)
            value = e.get("value", 0.5)
            if age > self._max_age_seconds:
                pr.removed_count += 1
                pr.pruning_reasons["expired"] = pr.pruning_reasons.get("expired", 0) + 1
            elif value < self._min_value:
                pr.removed_count += 1
                pr.pruning_reasons["low_value"] = pr.pruning_reasons.get("low_value", 0) + 1
            else:
                pr.kept_count += 1
        return pr

    def calculate_value(self, entry: Dict[str, Any]) -> float:
        """Calculate entry value based on multiple factors."""
        score = entry.get("score", 0.5)
        hits = entry.get("hits", 0)
        recency = entry.get("recency_score", 0.5)
        return round(0.4 * score + 0.3 * min(hits / 10.0, 1.0) + 0.3 * recency, 3)
