"""provider_timeout.py — Timeout management for providers."""
from __future__ import annotations
from typing import Any, Dict


class ProviderTimeout:
    """Manages timeouts for provider requests."""

    def __init__(self, default_timeout: float = 60.0) -> None:
        self._default_timeout = default_timeout
        self._timeouts: Dict[str, float] = {}

    def set_timeout(self, provider: str, timeout: float) -> None:
        self._timeouts[provider] = timeout

    def get_timeout(self, provider: str) -> float:
        return self._timeouts.get(provider, self._default_timeout)

    def set_default(self, timeout: float) -> None:
        self._default_timeout = timeout

    def to_dict(self) -> Dict[str, Any]:
        return {"default": self._default_timeout, "overrides": dict(self._timeouts)}
