"""Thread-safe function profiler with nested/concurrent call safety."""
from __future__ import annotations

import functools
import threading
import time
from typing import Any, Callable, Dict, List, Optional


class ProfileEntry:
    __slots__ = ("function_name", "total_calls", "total_time_ms",
                 "min_time_ms", "max_time_ms", "avg_time_ms", "errors")

    def __init__(self, function_name: str) -> None:
        self.function_name = function_name
        self.total_calls = 0
        self.total_time_ms = 0.0
        self.min_time_ms = float("inf")
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
                "min_ms": round(self.min_time_ms, 3) if self.total_calls else 0.0,
                "max_ms": round(self.max_time_ms, 3),
                "errors": self.errors}


class Profiler:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._profiles: Dict[str, ProfileEntry] = {}
        self._active = threading.local()

    def start(self, name: str) -> None:
        if not name:
            raise ValueError("profile name is required")
        active = getattr(self._active, "starts", None)
        if active is None:
            active = {}
            self._active.starts = active
        active.setdefault(name, []).append(time.perf_counter())

    def stop(self, name: str) -> float:
        active = getattr(self._active, "starts", {})
        starts = active.get(name)
        if not starts:
            raise RuntimeError(f"profile '{name}' was not started")
        duration_ms = (time.perf_counter() - starts.pop()) * 1000
        with self._lock:
            entry = self._profiles.setdefault(name, ProfileEntry(name))
            entry.record(duration_ms)
        return duration_ms

    def record_error(self, name: str) -> None:
        with self._lock:
            entry = self._profiles.setdefault(name, ProfileEntry(name))
            entry.errors += 1

    def profile(self, func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            self.start(func.__qualname__)
            try:
                return func(*args, **kwargs)
            except Exception:
                self.record_error(func.__qualname__)
                raise
            finally:
                self.stop(func.__qualname__)
        return wrapper

    def get_profile(self, name: str) -> Optional[ProfileEntry]:
        with self._lock:
            return self._profiles.get(name)

    def list_profiles(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [p.to_dict() for p in self._profiles.values()]

    def summary(self) -> Dict[str, Any]:
        with self._lock:
            return {"functions": len(self._profiles),
                    "total_calls": sum(p.total_calls for p in self._profiles.values()),
                    "total_time_ms": round(sum(p.total_time_ms for p in self._profiles.values()), 3)}

    def reset(self) -> None:
        with self._lock:
            self._profiles.clear()
        self._active = threading.local()
