"""provider_analytics.py — Analytics and usage tracking."""
from __future__ import annotations
import time
from typing import Any, Dict


class ProviderAnalytics:
    """Tracks analytics across all providers."""

    def __init__(self) -> None:
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._global_stats: Dict[str, Any] = {"total_requests": 0, "total_tokens": 0,
                                                "total_cost": 0.0, "start_time": time.time()}

    def start_session(self, session_id: str, provider: str) -> None:
        self._sessions[session_id] = {"provider": provider, "requests": 0,
                                       "tokens": 0, "cost": 0.0,
                                       "start_time": time.time()}

    def record(self, session_id: str, tokens: int = 0, cost: float = 0.0,
               latency_ms: float = 0.0) -> None:
        session = self._sessions.get(session_id)
        if session:
            session["requests"] += 1
            session["tokens"] += tokens
            session["cost"] += cost
        self._global_stats["total_requests"] += 1
        self._global_stats["total_tokens"] += tokens
        self._global_stats["total_cost"] += cost

    def end_session(self, session_id: str) -> Dict[str, Any]:
        return self._sessions.pop(session_id, {})

    def get_session(self, session_id: str) -> Dict[str, Any]:
        return dict(self._sessions.get(session_id, {}))

    def get_global_stats(self) -> Dict[str, Any]:
        return dict(self._global_stats)

    def get_provider_stats(self, provider: str) -> Dict[str, Any]:
        stats = {"requests": 0, "tokens": 0, "cost": 0.0}
        for s in self._sessions.values():
            if s["provider"] == provider:
                stats["requests"] += s["requests"]
                stats["tokens"] += s["tokens"]
                stats["cost"] += s["cost"]
        return stats

    def to_dict(self) -> Dict[str, Any]:
        return {"global": self.get_global_stats(), "sessions": len(self._sessions)}
