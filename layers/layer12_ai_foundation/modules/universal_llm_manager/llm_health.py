"""LLMHealth — Health checking for LLM providers."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class ProviderHealth:
    __slots__ = ("provider", "healthy", "latency_ms", "error_rate", "last_check")
    def __init__(self, provider: str = "") -> None:
        self.provider = provider; self.healthy = True; self.latency_ms = 0.0
        self.error_rate = 0.0; self.last_check = time.time()

class LLMHealth:
    def __init__(self) -> None:
        self._checks: Dict[str, ProviderHealth] = {}
    def check(self, provider: str, healthy: bool = True, latency_ms: float = 0.0) -> ProviderHealth:
        h = ProviderHealth(provider)
        h.healthy = healthy; h.latency_ms = latency_ms
        self._checks[provider] = h
        return h
    def is_healthy(self, provider: str = "") -> bool:
        if provider:
            h = self._checks.get(provider)
            return h.healthy if h else False
        return all(h.healthy for h in self._checks.values()) if self._checks else True
    def get_all(self) -> List[ProviderHealth]:
        return list(self._checks.values())
    def get_stats(self) -> Dict[str, Any]:
        healthy = sum(1 for h in self._checks.values() if h.healthy)
        return {"total": len(self._checks), "healthy": healthy, "unhealthy": len(self._checks) - healthy}
