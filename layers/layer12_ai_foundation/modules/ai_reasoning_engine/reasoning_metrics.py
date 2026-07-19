"""ReasoningMetrics — track reasoning engine performance."""
from __future__ import annotations

import time
from typing import Any, Dict


class ReasoningMetrics:
    """Track metrics for the reasoning engine."""

    def __init__(self) -> None:
        self.total_reasoning: int = 0
        self.by_type: Dict[str, int] = {}
        self.total_confidence: float = 0.0
        self.total_latency_ms: float = 0.0
        self.verified_count: int = 0
        self._start_time = time.time()

    def record(self, reasoning_type: str, confidence: float,
               latency_ms: float) -> None:
        self.total_reasoning += 1
        self.by_type[reasoning_type] = self.by_type.get(reasoning_type, 0) + 1
        self.total_confidence += confidence
        self.total_latency_ms += latency_ms

    def record_verification(self, passed: bool) -> None:
        if passed:
            self.verified_count += 1

    @property
    def avg_confidence(self) -> float:
        return self.total_confidence / max(self.total_reasoning, 1)

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / max(self.total_reasoning, 1)

    @property
    def verification_rate(self) -> float:
        return self.verified_count / max(self.total_reasoning, 1)

    def reset(self) -> None:
        self.__init__()

    def to_dict(self) -> Dict[str, Any]:
        return {"total_reasoning": self.total_reasoning, "by_type": self.by_type,
                "avg_confidence": round(self.avg_confidence, 4),
                "avg_latency_ms": round(self.avg_latency_ms, 2),
                "verification_rate": round(self.verification_rate, 4)}
