"""provider_metrics.py — Provider performance metrics."""
from __future__ import annotations
import time
from typing import Any, Dict


class ProviderMetrics:
    """Tracks per-provider performance metrics."""

    def __init__(self) -> None:
        self._data: Dict[str, Dict[str, Any]] = {}

    def record(self, provider: str, latency_ms: float, tokens: int,
               cost: float, success: bool) -> None:
        if provider not in self._data:
            self._data[provider] = {"requests": 0, "errors": 0, "total_tokens": 0,
                                     "total_cost": 0.0, "total_latency_ms": 0.0,
                                     "avg_latency_ms": 0.0, "last_request": 0.0}
        d = self._data[provider]
        d["requests"] += 1
        if not success:
            d["errors"] += 1
        d["total_tokens"] += tokens
        d["total_cost"] += cost
        d["total_latency_ms"] += latency_ms
        d["avg_latency_ms"] = d["total_latency_ms"] / d["requests"]
        d["last_request"] = time.time()

    def get(self, provider: str) -> Dict[str, Any]:
        return dict(self._data.get(provider, {}))

    def get_all(self) -> Dict[str, Dict[str, Any]]:
        return {k: dict(v) for k, v in self._data.items()}

    def get_error_rate(self, provider: str) -> float:
        d = self._data.get(provider, {})
        reqs = d.get("requests", 0)
        return d.get("errors", 0) / reqs if reqs > 0 else 0.0

    def get_success_rate(self, provider: str) -> float:
        return 1.0 - self.get_error_rate(provider)

    def get_total_cost(self) -> float:
        return sum(d.get("total_cost", 0.0) for d in self._data.values())

    def reset(self, provider: str = "") -> None:
        if provider:
            self._data.pop(provider, None)
        else:
            self._data.clear()

    def to_dict(self) -> Dict[str, Any]:
        return self.get_all()
