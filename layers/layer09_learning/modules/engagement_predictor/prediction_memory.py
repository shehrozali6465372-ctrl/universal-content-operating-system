"""Prediction Memory — Store predictions and compare with actual outcomes."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_PM_COUNTER = itertools.count(1)


class PredictionRecord:
    """A stored prediction for later comparison."""

    __slots__ = ("record_id", "content_id", "predicted", "actual",
                 "platform", "content_type", "timestamp", "compared")

    def __init__(self, content_id: str = "") -> None:
        self.record_id: str = f"pr_{next(_PM_COUNTER)}"
        self.content_id = content_id
        self.predicted: Dict[str, float] = {}
        self.actual: Optional[Dict[str, float]] = None
        self.platform: str = ""
        self.content_type: str = ""
        self.timestamp: float = time.time()
        self.compared: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "content_id": self.content_id,
            "predicted": self.predicted,
            "actual": self.actual,
            "platform": self.platform,
            "compared": self.compared,
        }


class PredictionMemory:
    """Store and retrieve predictions, compare with actual outcomes."""

    def __init__(self, max_entries: int = 10000) -> None:
        self._max_entries = max_entries
        self._records: List[PredictionRecord] = []

    def store(self, content_id: str, predicted: Dict[str, float],
              platform: str = "", content_type: str = "") -> PredictionRecord:
        record = PredictionRecord(content_id)
        record.predicted = dict(predicted)
        record.platform = platform
        record.content_type = content_type
        self._records.append(record)
        if len(self._records) > self._max_entries:
            self._records = self._records[-self._max_entries:]
        return record

    def record_actual(self, record_id: str, actual: Dict[str, float]) -> Optional[PredictionRecord]:
        for r in self._records:
            if r.record_id == record_id:
                r.actual = dict(actual)
                r.compared = True
                return r
        return None

    def record_actual_by_content(self, content_id: str, actual: Dict[str, float]) -> Optional[PredictionRecord]:
        for r in reversed(self._records):
            if r.content_id == content_id and not r.compared:
                r.actual = dict(actual)
                r.compared = True
                return r
        return None

    def get_comparisons(self, platform: str = "", limit: int = 50) -> List[PredictionRecord]:
        results = [r for r in self._records if r.compared]
        if platform:
            results = [r for r in results if r.platform.lower() == platform.lower()]
        return results[-limit:]

    def get_uncompared(self, limit: int = 50) -> List[PredictionRecord]:
        return [r for r in self._records if not r.compared][-limit:]

    def get_by_content(self, content_id: str) -> List[PredictionRecord]:
        return [r for r in self._records if r.content_id == content_id]

    def compute_accuracy(self, platform: str = "") -> Dict[str, Any]:
        comparisons = self.get_comparisons(platform)
        if not comparisons:
            return {"count": 0, "avg_error": 0.0, "accuracy": 0.0}

        total_error = 0.0
        count = 0
        for r in comparisons:
            if r.actual is None:
                continue
            for key in r.predicted:
                if key in r.actual and r.actual[key] > 0:
                    error = abs(r.predicted[key] - r.actual[key]) / r.actual[key]
                    total_error += error
                    count += 1

        if count == 0:
            return {"count": 0, "avg_error": 0.0, "accuracy": 0.0}

        avg_error = total_error / count
        return {
            "count": len(comparisons),
            "avg_error": round(avg_error, 4),
            "accuracy": round(max(0.0, 1.0 - avg_error), 4),
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total": len(self._records),
            "compared": sum(1 for r in self._records if r.compared),
            "uncompared": sum(1 for r in self._records if not r.compared),
        }

    @property
    def record_count(self) -> int:
        return len(self._records)
