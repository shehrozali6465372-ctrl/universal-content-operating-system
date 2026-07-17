"""Learning Signal — Data model for learning signals."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, Optional

_SIGNAL_COUNTER = itertools.count(1)

SIGNAL_SOURCES = ("analytics", "human", "platform", "system", "ab_test")
SIGNAL_TYPES = ("engagement", "conversion", "reach", "growth", "failure", "success", "anomaly")


class LearningSignal:
    """A single learning signal from any source."""

    __slots__ = (
        "signal_id", "source", "signal_type", "metric_name",
        "value", "previous_value", "confidence", "context",
        "timestamp", "platform", "content_id", "metadata",
    )

    def __init__(
        self,
        source: str = "analytics",
        signal_type: str = "engagement",
        metric_name: str = "",
        value: float = 0.0,
    ) -> None:
        self.signal_id: str = f"sig_{next(_SIGNAL_COUNTER)}"
        self.source = source if source in SIGNAL_SOURCES else "system"
        self.signal_type = signal_type if signal_type in SIGNAL_TYPES else "engagement"
        self.metric_name = metric_name
        self.value = value
        self.previous_value: Optional[float] = None
        self.confidence: float = 0.8
        self.context: Dict[str, Any] = {}
        self.timestamp: float = time.time()
        self.platform: str = ""
        self.content_id: str = ""
        self.metadata: Dict[str, Any] = {}

    @property
    def change(self) -> Optional[float]:
        if self.previous_value is not None:
            return self.value - self.previous_value
        return None

    @property
    def change_pct(self) -> Optional[float]:
        if self.previous_value is not None and self.previous_value != 0:
            return ((self.value - self.previous_value) / abs(self.previous_value)) * 100
        return None

    def is_positive(self) -> bool:
        c = self.change
        if c is None:
            return self.value > 0
        return c > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "source": self.source,
            "signal_type": self.signal_type,
            "metric_name": self.metric_name,
            "value": self.value,
            "previous_value": self.previous_value,
            "change": self.change,
            "confidence": round(self.confidence, 3),
            "platform": self.platform,
            "timestamp": self.timestamp,
        }
