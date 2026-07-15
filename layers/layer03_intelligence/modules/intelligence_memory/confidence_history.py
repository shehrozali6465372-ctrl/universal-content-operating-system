"""Confidence History — Track confidence scores over time."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional


class ConfidenceRecord:
    """A single confidence record."""
    __slots__ = ("record_id", "topic", "module", "confidence", "reasons",
                 "components", "timestamp", "context")

    def __init__(self, topic: str = "", module: str = "", confidence: float = 0.5) -> None:
        self.record_id = f"crec_{next(_CONF_COUNTER)}"
        self.topic = topic
        self.module = module
        self.confidence = confidence
        self.reasons: List[str] = []
        self.components: Dict[str, float] = {}
        self.timestamp = time.time()
        self.context: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "topic": self.topic,
            "module": self.module,
            "confidence": round(self.confidence, 3),
            "reasons": self.reasons,
            "components": {k: round(v, 3) for k, v in self.components.items()},
        }


_CONF_COUNTER = itertools.count(1)


class ConfidenceHistory:
    """Tracks confidence scores over time for analysis."""

    def __init__(self) -> None:
        self._records: List[ConfidenceRecord] = []
        self._topic_index: Dict[str, List[int]] = {}
        self._module_index: Dict[str, List[int]] = {}

    def record(self, topic: str, module: str, confidence: float,
               reasons: Optional[List[str]] = None,
               components: Optional[Dict[str, float]] = None,
               context: Optional[Dict] = None) -> ConfidenceRecord:
        """Record a confidence measurement."""
        cr = ConfidenceRecord(topic=topic, module=module, confidence=confidence)
        cr.reasons = reasons or []
        cr.components = components or {}
        cr.context = context or {}
        idx = len(self._records)
        self._records.append(cr)
        self._topic_index.setdefault(topic, []).append(idx)
        self._module_index.setdefault(module, []).append(idx)
        return cr

    def get_topic_history(self, topic: str) -> List[ConfidenceRecord]:
        idxs = self._topic_index.get(topic, [])
        return [self._records[i] for i in idxs if i < len(self._records)]

    def get_module_history(self, module: str) -> List[ConfidenceRecord]:
        idxs = self._module_index.get(module, [])
        return [self._records[i] for i in idxs if i < len(self._records)]

    def get_trend(self, topic: str) -> Dict[str, Any]:
        """Get confidence trend for a topic."""
        history = self.get_topic_history(topic)
        if not history:
            return {"topic": topic, "trend": "unknown", "data_points": 0}
        values = [r.confidence for r in history]
        avg = sum(values) / len(values)
        if len(values) >= 2:
            slope = (values[-1] - values[0]) / max(len(values) - 1, 1)
            if slope > 0.05:
                trend = "improving"
            elif slope < -0.05:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        return {
            "topic": topic,
            "trend": trend,
            "avg_confidence": round(avg, 3),
            "min": round(min(values), 3),
            "max": round(max(values), 3),
            "data_points": len(values),
        }

    def get_average_by_module(self) -> Dict[str, float]:
        """Get average confidence per module."""
        result: Dict[str, Dict] = {}
        for r in self._records:
            if r.module not in result:
                result[r.module] = {"total": 0.0, "count": 0}
            result[r.module]["total"] += r.confidence
            result[r.module]["count"] += 1
        return {m: round(d["total"] / max(d["count"], 1), 3) for m, d in result.items()}

    def get_latest(self, topic: str, module: Optional[str] = None) -> Optional[ConfidenceRecord]:
        history = self.get_topic_history(topic)
        if module:
            history = [r for r in history if r.module == module]
        return history[-1] if history else None

    @property
    def count(self) -> int:
        return len(self._records)
