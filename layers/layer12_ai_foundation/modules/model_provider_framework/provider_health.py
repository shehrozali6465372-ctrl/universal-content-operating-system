"""provider_health.py — Provider health monitoring."""
from __future__ import annotations
import time
from typing import Any, Dict


class ProviderHealth:
    """Monitors health of each provider."""

    def __init__(self) -> None:
        self._health: Dict[str, Dict[str, Any]] = {}

    def check(self, provider_name: str, is_available: bool,
              latency_ms: float = 0.0) -> Dict[str, Any]:
        if provider_name not in self._health:
            self._health[provider_name] = {"checks": 0, "failures": 0,
                                             "last_check": 0.0, "status": "unknown",
                                             "avg_latency_ms": 0.0}
        h = self._health[provider_name]
        h["checks"] += 1
        if not is_available:
            h["failures"] += 1
        h["status"] = "healthy" if is_available else "unhealthy"
        h["last_check"] = time.time()
        total = h["avg_latency_ms"] * (h["checks"] - 1)
        h["avg_latency_ms"] = (total + latency_ms) / h["checks"]
        return dict(h)

    def get(self, provider_name: str) -> Dict[str, Any]:
        return dict(self._health.get(provider_name, {"status": "unknown"}))

    def is_healthy(self, provider_name: str) -> bool:
        return self.get(provider_name).get("status") == "healthy"

    def get_all(self) -> Dict[str, Dict[str, Any]]:
        return {k: dict(v) for k, v in self._health.items()}

    def get_failure_rate(self, provider_name: str) -> float:
        h = self._health.get(provider_name, {})
        checks = h.get("checks", 0)
        return h.get("failures", 0) / checks if checks > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return self.get_all()
