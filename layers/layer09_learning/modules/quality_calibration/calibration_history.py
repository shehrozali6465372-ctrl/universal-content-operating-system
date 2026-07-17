"""Calibration History — Track calibration changes over time."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List

_CH_COUNTER = itertools.count(1)


class CalibrationHistoryEntry:
    """A single calibration history entry."""

    __slots__ = ("entry_id", "metric", "old_bias", "new_bias",
                 "old_weight", "new_weight", "trigger", "timestamp")

    def __init__(self, metric: str = "") -> None:
        self.entry_id: str = f"ch_{next(_CH_COUNTER)}"
        self.metric = metric
        self.old_bias: float = 0.0
        self.new_bias: float = 0.0
        self.old_weight: float = 1.0
        self.new_weight: float = 1.0
        self.trigger: str = ""
        self.timestamp: float = time.time()

    @property
    def bias_change(self) -> float:
        return round(self.new_bias - self.old_bias, 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "metric": self.metric,
            "old_bias": round(self.old_bias, 4),
            "new_bias": round(self.new_bias, 4),
            "bias_change": self.bias_change,
            "trigger": self.trigger,
        }


class CalibrationHistory:
    """Track calibration changes over time."""

    def __init__(self) -> None:
        self._entries: List[CalibrationHistoryEntry] = []

    def record(self, metric: str, old_bias: float, new_bias: float,
               old_weight: float = 1.0, new_weight: float = 1.0,
               trigger: str = "auto") -> CalibrationHistoryEntry:
        entry = CalibrationHistoryEntry(metric)
        entry.old_bias = old_bias
        entry.new_bias = new_bias
        entry.old_weight = old_weight
        entry.new_weight = new_weight
        entry.trigger = trigger
        self._entries.append(entry)
        return entry

    def get_metric_history(self, metric: str) -> List[CalibrationHistoryEntry]:
        return [e for e in self._entries if e.metric == metric]

    def get_recent(self, count: int = 10) -> List[CalibrationHistoryEntry]:
        return list(self._entries[-count:])

    def get_by_trigger(self, trigger: str) -> List[CalibrationHistoryEntry]:
        return [e for e in self._entries if e.trigger == trigger]

    def get_latest(self, metric: str) -> CalibrationHistoryEntry | None:
        entries = self.get_metric_history(metric)
        return entries[-1] if entries else None

    @property
    def entry_count(self) -> int:
        return len(self._entries)
