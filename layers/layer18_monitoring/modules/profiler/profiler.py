"""Profiler — code execution profiling and timing."""
from __future__ import annotations
import time
import functools
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class ProfileEntry:
    __slots__ = ("function_name", "total_calls", "total_time_ms",
                 "min_time_ms", "max_time_ms", "avg_time_ms", "errors")

    def __init__(self, function_name: str) -> None:
        self.function_name = function_name
        self.total_calls = 0
        self.total_time_ms = 0.0
        self.min_time_ms = float('inf')
        self.max_time_ms = 0.0
        self.avg_time_ms = 0.0
        self.errors = 0

    def record(self, duration_ms: float, is_error: bool = False) -> None:
        self.total_calls += 1
        self.total_time_ms += duration_ms
        self.min_time_ms = min(self.min_time_ms, duration_ms)
        self.max_time_ms = max(self.max_time_ms, duration_ms)
        self.avg_time_ms = self.total_time_ms / self.total_calls
        if is_error:
            self.errors += 1

    def to_dict(self) -> Dict[str, Any]:
        return {"function": self.function_name, "calls": self.total_calls,
                "total_ms": round(self.total_time_ms, 3),
                "avg_ms": round(self.avg_time_ms, 3),
                "min_ms": round(self.min_time_ms, 3),
                "max_ms": round(self.max_time_ms, 3),
                "errors": self.errors}


class Profiler:
    def __init__(self) -> None:
        self._profiles: Dict[str, ProfileEntry] = {}
        self._active: Dict[str, float] = {}

    def start(self, name: str) -> None:
        self._active[name] = time.time()

    def stop(self, name: str) -> float:
        start = self._active.pop(name, time.time())
        duration_ms = (time.time() - start) * 1000
        if name not in self._profiles:
            self._profiles[name] = ProfileEntry(name)
        self._profiles[name].record(duration_ms)
        return duration_ms

    def record_error(self, name: str) -> None:
        if name not in self._profiles:
            self._profiles[name] = ProfileEntry(name)
        self._profiles[name].errors += 1

    def profile(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            self.start(func.__name__)
            try:
                result = func(*args, **kwargs)
                self.stop(func.__name__)
                return result
            except Exception:
                self.record_error(func.__name__)
                self.stop(func.__name__)
                raise
        return wrapper

    def get_profile(self, name: str) -> Optional[ProfileEntry]:
        return self._profiles.get(name)

    def list_profiles(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._profiles.values()]

    def summary(self) -> Dict[str, Any]:
        total_calls = sum(p.total_calls for p in self._profiles.values())
        total_time = sum(p.total_time_ms for p in self._profiles.values())
        return {"functions": len(self._profiles), "total_calls": total_calls,
                "total_time_ms": round(total_time, 3)}

    def reset(self) -> None:
        self._profiles.clear()
        self._active.clear()
