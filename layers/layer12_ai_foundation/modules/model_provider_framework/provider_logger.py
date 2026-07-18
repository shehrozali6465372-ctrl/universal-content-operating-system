"""provider_logger.py — Structured logging for providers."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class ProviderLogger:
    """Structured logger for provider operations."""

    def __init__(self) -> None:
        self._entries: List[Dict[str, Any]] = []
        self._max_entries: int = 10000

    def log(self, level: str, provider: str, message: str,
            details: Dict[str, Any] = None) -> None:
        entry = {"level": level, "provider": provider, "message": message,
                 "details": details or {}, "timestamp": time.time()}
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]

    def info(self, provider: str, message: str, **kwargs: Any) -> None:
        self.log("info", provider, message, kwargs)

    def warning(self, provider: str, message: str, **kwargs: Any) -> None:
        self.log("warning", provider, message, kwargs)

    def error(self, provider: str, message: str, **kwargs: Any) -> None:
        self.log("error", provider, message, kwargs)

    def debug(self, provider: str, message: str, **kwargs: Any) -> None:
        self.log("debug", provider, message, kwargs)

    def get_entries(self, provider: str = "", level: str = "",
                    limit: int = 100) -> List[Dict[str, Any]]:
        entries = self._entries
        if provider:
            entries = [e for e in entries if e["provider"] == provider]
        if level:
            entries = [e for e in entries if e["level"] == level]
        return entries[-limit:]

    def clear(self) -> None:
        self._entries.clear()

    def get_stats(self) -> Dict[str, Any]:
        levels: Dict[str, int] = {}
        for e in self._entries:
            levels[e["level"]] = levels.get(e["level"], 0) + 1
        return {"total_entries": len(self._entries), "by_level": levels}
