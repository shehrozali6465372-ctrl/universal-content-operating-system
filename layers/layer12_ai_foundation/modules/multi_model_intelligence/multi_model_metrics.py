"""MultiModelMetrics — track multi-model intelligence metrics."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional


class MultiModelMetrics:
    """Track metrics for multi-model operations."""

    def __init__(self) -> None:
        self.total_requests: int = 0
        self.successful_requests: int = 0
        self.failed_requests: int = 0
        self.total_models_used: int = 0
        self.total_tokens: int = 0
        self.total_latency_ms: float = 0.0
        self.consensus_scores: List[float] = []
        self.model_usage: Dict[str, int] = {}
        self._start_time = time.time()

    def record_request(self, models_used: int, success: bool,
                       latency_ms: float = 0.0, tokens: int = 0,
                       consensus_score: float = 0.0,
                       model_names: Optional[List[str]] = None) -> None:
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        self.total_models_used += models_used
        self.total_tokens += tokens
        self.total_latency_ms += latency_ms
        self.consensus_scores.append(consensus_score)
        if model_names:
            for name in model_names:
                self.model_usage[name] = self.model_usage.get(name, 0) + 1

    @property
    def success_rate(self) -> float:
        return self.successful_requests / max(self.total_requests, 1)

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / max(self.total_requests, 1)

    @property
    def avg_consensus(self) -> float:
        return sum(self.consensus_scores) / max(len(self.consensus_scores), 1)

    def reset(self) -> None:
        self.__init__()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "success_rate": self.success_rate,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "avg_consensus": round(self.avg_consensus, 4),
            "total_tokens": self.total_tokens,
            "model_usage": self.model_usage,
        }
