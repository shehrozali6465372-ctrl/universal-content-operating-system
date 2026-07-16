"""Failure Memory — Remember recurring failures and best recovery strategies."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer07_publishing.modules.failure_recovery.failure_detector import FailureRecord


class FailurePattern:
    """A recognized recurring failure pattern."""

    __slots__ = ("pattern_id", "error_type", "platform", "count",
                 "best_recovery", "success_rate", "last_seen")

    def __init__(self, error_type: str, platform: str = "") -> None:
        self.pattern_id: str = f"pat_{error_type}_{platform}".replace(" ", "_")
        self.error_type = error_type
        self.platform = platform
        self.count: int = 0
        self.best_recovery: str = "retry_exponential"
        self.success_rate: float = 0.0
        self.last_seen: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "error_type": self.error_type,
            "platform": self.platform,
            "count": self.count,
            "best_recovery": self.best_recovery,
            "success_rate": round(self.success_rate, 3),
            "last_seen": self.last_seen,
        }


class FailureMemory:
    """Remember recurring failures and learn from them."""

    def __init__(self) -> None:
        self._patterns: Dict[str, FailurePattern] = {}
        self._total_observations = 0

    def observe(self, record: FailureRecord, recovered: bool = False) -> FailurePattern:
        key = f"{record.error_type}_{record.platform}"
        if key not in self._patterns:
            self._patterns[key] = FailurePattern(record.error_type, record.platform)
        pat = self._patterns[key]
        pat.count += 1
        pat.last_seen = time.time()

        total = pat.count
        successes = pat.success_rate * (total - 1) + (1 if recovered else 0)
        pat.success_rate = successes / total
        self._total_observations += 1
        return pat

    def update_best_recovery(self, error_type: str, platform: str, strategy: str) -> None:
        key = f"{error_type}_{platform}"
        if key in self._patterns:
            self._patterns[key].best_recovery = strategy

    def get_pattern(self, error_type: str, platform: str = "") -> Optional[FailurePattern]:
        key = f"{error_type}_{platform}"
        return self._patterns.get(key)

    def get_recurring(self, min_count: int = 3) -> List[FailurePattern]:
        return [p for p in self._patterns.values() if p.count >= min_count]

    def get_best_strategy(self, error_type: str, platform: str = "") -> str:
        pat = self.get_pattern(error_type, platform)
        if pat and pat.count >= 2:
            return pat.best_recovery
        return "retry_exponential"

    def get_all_patterns(self) -> List[FailurePattern]:
        return list(self._patterns.values())

    def get_stats(self) -> Dict[str, Any]:
        patterns = list(self._patterns.values())
        recurring = [p for p in patterns if p.count >= 3]
        return {
            "total_patterns": len(patterns),
            "total_observations": self._total_observations,
            "recurring_patterns": len(recurring),
            "platforms": list(set(p.platform for p in patterns if p.platform)),
        }

    @property
    def pattern_count(self) -> int:
        return len(self._patterns)
