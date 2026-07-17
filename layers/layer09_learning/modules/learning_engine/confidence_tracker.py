"""Confidence Tracker — Track confidence evolution and learning quality."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class ConfidenceRecord:
    """A single confidence measurement."""

    __slots__ = ("metric_name", "confidence", "reliability", "timestamp",
                 "source", "context")

    def __init__(self, metric_name: str = "", confidence: float = 0.0) -> None:
        self.metric_name = metric_name
        self.confidence = confidence
        self.reliability: float = 0.5
        self.timestamp: float = time.time()
        self.source: str = ""
        self.context: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "confidence": round(self.confidence, 3),
            "reliability": round(self.reliability, 3),
            "timestamp": self.timestamp,
        }


class ConfidenceTracker:
    """Track confidence evolution over time."""

    def __init__(self) -> None:
        self._records: Dict[str, List[ConfidenceRecord]] = {}
        self._tracking_count = 0

    def record(self, metric_name: str, confidence: float, reliability: float = 0.5,
               source: str = "") -> ConfidenceRecord:
        rec = ConfidenceRecord(metric_name, confidence)
        rec.reliability = reliability
        rec.source = source
        self._records.setdefault(metric_name, []).append(rec)
        self._tracking_count += 1
        return rec

    def get_current_confidence(self, metric_name: str) -> float:
        records = self._records.get(metric_name, [])
        if not records:
            return 0.0
        return records[-1].confidence

    def get_avg_confidence(self, metric_name: str) -> float:
        records = self._records.get(metric_name, [])
        if not records:
            return 0.0
        return round(sum(r.confidence for r in records) / len(records), 3)

    def get_trend(self, metric_name: str) -> str:
        records = self._records.get(metric_name, [])
        if len(records) < 2:
            return "insufficient_data"
        recent = [r.confidence for r in records[-5:]]
        if len(recent) >= 2:
            if recent[-1] > recent[0] * 1.05:
                return "improving"
            elif recent[-1] < recent[0] * 0.95:
                return "declining"
        return "stable"

    def get_all_metrics(self) -> List[str]:
        return list(self._records.keys())

    def get_history(self, metric_name: str, limit: int = 20) -> List[ConfidenceRecord]:
        return self._records.get(metric_name, [])[-limit:]

    def get_overall_reliability(self) -> float:
        all_reliabilities = []
        for records in self._records.values():
            for r in records:
                all_reliabilities.append(r.reliability)
        if not all_reliabilities:
            return 0.0
        return round(sum(all_reliabilities) / len(all_reliabilities), 3)

    @property
    def tracking_count(self) -> int:
        return self._tracking_count
