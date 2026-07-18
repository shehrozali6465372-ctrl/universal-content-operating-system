"""LLMMetrics — Track LLM usage, cost, latency."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class LLMMetrics:
    def __init__(self) -> None:
        self._requests: int = 0
        self._tokens_used: int = 0
        self._total_cost: float = 0.0
        self._latencies: List[float] = []
        self._errors: int = 0
        self._by_provider: Dict[str, int] = {}
        self._by_model: Dict[str, int] = {}

    def record_request(self, provider: str, model: str, tokens: int,
                       cost: float, latency_ms: float, success: bool = True) -> None:
        self._requests += 1
        self._tokens_used += tokens
        self._total_cost += cost
        self._latencies.append(latency_ms)
        if len(self._latencies) > 10000:
            self._latencies = self._latencies[-10000:]
        if not success:
            self._errors += 1
        self._by_provider[provider] = self._by_provider.get(provider, 0) + 1
        self._by_model[model] = self._by_model.get(model, 0) + 1

    def get_avg_latency(self) -> float:
        if not self._latencies:
            return 0.0
        return round(sum(self._latencies) / len(self._latencies), 2)

    def get_error_rate(self) -> float:
        if self._requests == 0:
            return 0.0
        return round(self._errors / self._requests, 4)

    def get_tokens_per_request(self) -> float:
        if self._requests == 0:
            return 0.0
        return round(self._tokens_used / self._requests, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {"requests": self._requests, "tokens_used": self._tokens_used,
                "total_cost": round(self._total_cost, 4),
                "avg_latency_ms": self.get_avg_latency(),
                "error_rate": self.get_error_rate(),
                "by_provider": dict(self._by_provider),
                "by_model": dict(self._by_model)}

    def reset(self) -> None:
        self._requests = 0; self._tokens_used = 0; self._total_cost = 0.0
        self._latencies.clear(); self._errors = 0
        self._by_provider.clear(); self._by_model.clear()
