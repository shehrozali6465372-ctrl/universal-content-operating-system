"""provider_limits.py — Provider rate limits and quotas."""
from __future__ import annotations
import time
from typing import Any, Dict

DEFAULT_LIMITS: Dict[str, Dict[str, Any]] = {
    "openai": {"rpm": 500, "tpm": 150000, "rpd": 10000},
    "claude": {"rpm": 1000, "tpm": 100000, "rpd": 5000},
    "gemini": {"rpm": 600, "tpm": 100000, "rpd": 5000},
    "deepseek": {"rpm": 200, "tpm": 100000, "rpd": 5000},
    "mistral": {"rpm": 60, "tpm": 30000, "rpd": 1000},
    "cohere": {"rpm": 100, "tpm": 20000, "rpd": 1000},
    "grok": {"rpm": 60, "tpm": 30000, "rpd": 1000},
    "ollama": {"rpm": 9999, "tpm": 9999999, "rpd": 99999},
}


class ProviderLimits:
    """Manages rate limits per provider."""

    def __init__(self) -> None:
        self._limits: Dict[str, Dict[str, Any]] = dict(DEFAULT_LIMITS)
        self._usage: Dict[str, Dict[str, int]] = {}
        self._window_start: Dict[str, float] = {}

    def set_limits(self, provider: str, rpm: int = 0, tpm: int = 0, rpd: int = 0) -> None:
        limits: Dict[str, int] = {}
        if rpm > 0:
            limits["rpm"] = rpm
        if tpm > 0:
            limits["tpm"] = tpm
        if rpd > 0:
            limits["rpd"] = rpd
        self._limits[provider] = limits

    def check(self, provider: str, tokens: int = 0) -> bool:
        if provider not in self._usage:
            self._usage[provider] = {"requests": 0, "tokens": 0}
            self._window_start[provider] = time.time()
        usage = self._usage[provider]
        limits = self._limits.get(provider, {})
        if usage.get("requests", 0) >= limits.get("rpm", 9999):
            return False
        if usage.get("tokens", 0) + tokens > limits.get("tpm", 9999999):
            return False
        return True

    def record(self, provider: str, tokens: int = 0) -> None:
        if provider not in self._usage:
            self._usage[provider] = {"requests": 0, "tokens": 0}
        self._usage[provider]["requests"] = self._usage[provider].get("requests", 0) + 1
        self._usage[provider]["tokens"] = self._usage[provider].get("tokens", 0) + tokens

    def get_usage(self, provider: str) -> Dict[str, Any]:
        usage = dict(self._usage.get(provider, {"requests": 0, "tokens": 0}))
        limits = self._limits.get(provider, {})
        return {**usage, "limits": dict(limits)}

    def reset(self, provider: str = "") -> None:
        if provider:
            self._usage.pop(provider, None)
        else:
            self._usage.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {p: self.get_usage(p) for p in self._limits}
