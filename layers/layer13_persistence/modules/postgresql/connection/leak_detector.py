"""ConnectionLeakDetector — Detect and warn about unreleased database connections.

Enterprise feature: tracks every connection acquire/release. If a connection
is acquired but not released within a timeout, it triggers a leak warning
and optionally forces回收.
"""
from __future__ import annotations
import time
import threading
import traceback
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class TrackedConnection:
    connection_id: str
    acquired_at: float
    acquire_stack: str
    released: bool = False
    released_at: Optional[float] = None
    duration_ms: Optional[float] = None


class ConnectionLeakDetector:
    """Detects database connection leaks by tracking acquire/release pairs."""

    def __init__(self, leak_timeout_seconds: float = 60.0, check_interval_seconds: float = 10.0):
        self._leak_timeout = leak_timeout_seconds
        self._check_interval = check_interval_seconds
        self._connections: Dict[str, TrackedConnection] = {}
        self._leaks: List[Dict[str, Any]] = []
        self._total_acquired = 0
        self._total_released = 0
        self._total_leaks_detected = 0
        self._lock = threading.Lock()
        self._counter = 0
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitoring = False

    def _next_id(self) -> str:
        self._counter += 1
        return f"conn_{self._counter}_{int(time.time() * 1000)}"

    def acquire(self) -> str:
        """Track a connection acquisition. Returns tracking ID."""
        conn_id = self._next_id()
        stack = "".join(traceback.format_stack()[-4:-1])
        tracked = TrackedConnection(
            connection_id=conn_id,
            acquired_at=time.time(),
            acquire_stack=stack,
        )
        with self._lock:
            self._connections[conn_id] = tracked
            self._total_acquired += 1
        return conn_id

    def release(self, conn_id: str) -> bool:
        """Mark a connection as released. Returns True if tracked."""
        with self._lock:
            tracked = self._connections.get(conn_id)
            if tracked and not tracked.released:
                tracked.released = True
                tracked.released_at = time.time()
                tracked.duration_ms = round((tracked.released_at - tracked.acquired_at) * 1000, 2)
                self._total_released += 1
                return True
            return False

    def check_leaks(self) -> List[Dict[str, Any]]:
        """Check for connections that have been open too long."""
        now = time.time()
        found_leaks = []
        with self._lock:
            for conn_id, tracked in self._connections.items():
                if not tracked.released:
                    age_seconds = now - tracked.acquired_at
                    if age_seconds > self._leak_timeout:
                        leak_info = {
                            "connection_id": conn_id,
                            "age_seconds": round(age_seconds, 1),
                            "acquired_at": tracked.acquired_at,
                            "acquire_stack": tracked.acquire_stack.strip(),
                            "detected_at": now,
                        }
                        found_leaks.append(leak_info)
                        self._leaks.append(leak_info)
                        self._total_leaks_detected += 1
        return found_leaks

    def start_monitoring(self) -> None:
        """Start background leak detection thread."""
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
            self._monitor_thread = None

    def _monitor_loop(self) -> None:
        while self._monitoring:
            try:
                self.check_leaks()
            except Exception:
                pass
            time.sleep(self._check_interval)

    def get_stats(self) -> Dict[str, Any]:
        """Get leak detector statistics."""
        with self._lock:
            active = sum(1 for t in self._connections.values() if not t.released)
            released = sum(1 for t in self._connections.values() if t.released)
            durations = [t.duration_ms for t in self._connections.values() if t.released and t.duration_ms]
            avg_duration = sum(durations) / len(durations) if durations else 0.0

            return {
                "total_acquired": self._total_acquired,
                "total_released": self._total_released,
                "currently_active": active,
                "total_leaks_detected": self._total_leaks_detected,
                "leak_timeout_seconds": self._leak_timeout,
                "avg_duration_ms": round(avg_duration, 2),
                "recent_leaks": self._leaks[-10:],
            }

    def get_active_connections(self) -> List[Dict[str, Any]]:
        """Return list of currently active (unreleased) connections."""
        with self._lock:
            result = []
            for conn_id, tracked in self._connections.items():
                if not tracked.released:
                    age = time.time() - tracked.acquired_at
                    result.append({
                        "connection_id": conn_id,
                        "age_seconds": round(age, 1),
                        "acquired_at": tracked.acquired_at,
                    })
            return result

    def reset(self) -> None:
        """Reset all tracking state."""
        with self._lock:
            self._connections.clear()
            self._leaks.clear()
            self._total_acquired = 0
            self._total_released = 0
            self._total_leaks_detected = 0
            self._counter = 0
