"""TimeoutEngine — enforce timeouts on async operations."""
from __future__ import annotations
import asyncio
import time
import uuid
from typing import Any, Callable, Coroutine, Dict, List, Optional
from enum import Enum


class TimeoutResult(str, Enum):
    COMPLETED = "completed"; TIMED_OUT = "timed_out"; ERROR = "error"


class TimeoutEntry:
    __slots__ = ("entry_id", "name", "timeout_seconds", "result",
                 "started_at", "finished_at", "duration_ms", "metadata")

    def __init__(self, name: str, timeout_seconds: float) -> None:
        self.entry_id = str(uuid.uuid4())[:12]
        self.name = name
        self.timeout_seconds = timeout_seconds
        self.result = TimeoutResult.COMPLETED
        self.started_at = time.time()
        self.finished_at: float = 0.0
        self.duration_ms: float = 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"entry_id": self.entry_id, "name": self.name,
                "timeout_seconds": self.timeout_seconds, "result": self.result.value,
                "duration_ms": round(self.duration_ms, 2)}


class TimeoutEngine:
    def __init__(self) -> None:
        self._entries: Dict[str, TimeoutEntry] = {}
        self._history: List[Dict[str, Any]] = []

    async def run_with_timeout(self, coro_fn: Callable, timeout_seconds: float,
                               name: str = "operation", *args: Any, **kwargs: Any) -> Dict[str, Any]:
        entry = TimeoutEntry(name, timeout_seconds)
        self._entries[entry.entry_id] = entry
        try:
            coro = coro_fn(*args, **kwargs)
            if asyncio.iscoroutine(coro):
                result = await asyncio.wait_for(coro, timeout=timeout_seconds)
            else:
                result = coro
            entry.result = TimeoutResult.COMPLETED
            entry.finished_at = time.time()
            entry.duration_ms = (entry.finished_at - entry.started_at) * 1000
            self._history.append(entry.to_dict())
            return {"status": "completed", "result": result, "entry": entry.to_dict()}
        except asyncio.TimeoutError:
            entry.result = TimeoutResult.TIMED_OUT
            entry.finished_at = time.time()
            entry.duration_ms = (entry.finished_at - entry.started_at) * 1000
            self._history.append(entry.to_dict())
            return {"status": "timed_out", "entry": entry.to_dict()}
        except Exception as exc:
            entry.result = TimeoutResult.ERROR
            entry.finished_at = time.time()
            entry.duration_ms = (entry.finished_at - entry.started_at) * 1000
            self._history.append(entry.to_dict())
            return {"status": "error", "error": str(exc), "entry": entry.to_dict()}

    def get_entry(self, entry_id: str) -> Optional[TimeoutEntry]:
        return self._entries.get(entry_id)

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)

    def stats(self) -> Dict[str, Any]:
        results = {}
        for e in self._entries.values():
            results[e.result.value] = results.get(e.result.value, 0) + 1
        return {"total": len(self._entries), "results": results}
