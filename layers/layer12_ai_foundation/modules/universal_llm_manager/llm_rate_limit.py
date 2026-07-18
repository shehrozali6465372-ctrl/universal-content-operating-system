"""LLMRateLimit — Rate limiting for LLM calls."""
from __future__ import annotations
import time
from typing import Any, Dict

class LLMRateLimit:
    def __init__(self, requests_per_minute: int = 60, tokens_per_minute: int = 100000) -> None:
        self._rpm = requests_per_minute
        self._tpm = tokens_per_minute
        self._request_timestamps: list = []
        self._token_timestamps: list = []

    def check(self, tokens: int = 0) -> bool:
        now = time.time()
        self._request_timestamps = [t for t in self._request_timestamps if now - t < 60]
        self._token_timestamps = [(t, tok) for t, tok in self._token_timestamps if now - t < 60]
        if len(self._request_timestamps) >= self._rpm:
            return False
        current_tpm = sum(tok for _, tok in self._token_timestamps)
        if current_tpm + tokens > self._tpm:
            return False
        self._request_timestamps.append(now)
        self._token_timestamps.append((now, tokens))
        return True

    def get_stats(self) -> Dict[str, Any]:
        now = time.time()
        rpm = len([t for t in self._request_timestamps if now - t < 60])
        tpm = sum(tok for t, tok in self._token_timestamps if now - t < 60)
        return {"current_rpm": rpm, "max_rpm": self._rpm,
                "current_tpm": tpm, "max_tpm": self._tpm}
