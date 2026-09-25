"""Timeout enforcement with explicit validation and cancellation semantics."""
from __future__ import annotations

import asyncio
import inspect
import time
import uuid
from enum import Enum
from typing import Any, Callable


class TimeoutResult(str, Enum):
    COMPLETED = "completed"
    TIMED_OUT = "timed_out"
    ERROR = "error"


class TimeoutEntry:
    __slots__ = ("entry_id", "name", "timeout_seconds", "result",
                 "started_at", "finished_at", "duration_ms", "metadata")

    def __init__(self, name: str, timeout_seconds: float) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.entry_id = str(uuid.uuid4())
        self.name = name
        self.timeout_seconds = timeout_seconds
        self.result = TimeoutResult.COMPLETED
        self.started_at = time.time()
        self.finished_at = 0.0
        self.duration_ms = 0.0
        self.metadata: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id, "name": self.name,
            "timeout_seconds": self.timeout_seconds, "result": self.result.value,
            "duration_ms": round(self.duration_ms, 2),
        }


class TimeoutEngine:
    def __init__(self) -> None:
        self._entries: dict[str, TimeoutEntry] = {}
        self._history: list[dict[str, Any]] = []

    async def run_with_timeout(
        self, coro_fn: Callable[..., Any], timeout_seconds: float,
        name: str = "operation", *args: Any, **kwargs: Any,
    ) -> dict[str, Any]:
        entry = TimeoutEntry(name, timeout_seconds)
        self._entries[entry.entry_id] = entry
        try:
            value = coro_fn(*args, **kwargs)
            if inspect.isawaitable(value):
                result = await asyncio.wait_for(value, timeout=timeout_seconds)
            else:
                result = value
        except asyncio.TimeoutError:
            entry.result = TimeoutResult.TIMED_OUT
            entry.finished_at = time.time()
            entry.duration_ms = (entry.finished_at - entry.started_at) * 1000
            self._history.append(entry.to_dict())
            return {"status": "timed_out", "entry": entry.to_dict()}
        except asyncio.CancelledError:
            entry.result = TimeoutResult.ERROR
            entry.finished_at = time.time()
            entry.duration_ms = (entry.finished_at - entry.started_at) * 1000
            self._history.append(entry.to_dict())
            raise
        except Exception as exc:
            entry.result = TimeoutResult.ERROR
            entry.finished_at = time.time()
            entry.duration_ms = (entry.finished_at - entry.started_at) * 1000
            self._history.append(entry.to_dict())
            return {"status": "error", "error": f"{type(exc).__name__}: {exc}", "entry": entry.to_dict()}
        entry.result = TimeoutResult.COMPLETED
        entry.finished_at = time.time()
        entry.duration_ms = (entry.finished_at - entry.started_at) * 1000
        self._history.append(entry.to_dict())
        return {"status": "completed", "result": result, "entry": entry.to_dict()}

    def get_entry(self, entry_id: str) -> TimeoutEntry | None:
        return self._entries.get(entry_id)

    def get_history(self) -> list[dict[str, Any]]:
        return list(self._history)

    def stats(self) -> dict[str, Any]:
        results: dict[str, int] = {}
        for entry in self._entries.values():
            results[entry.result.value] = results.get(entry.result.value, 0) + 1
        return {"total": len(self._entries), "results": results}
