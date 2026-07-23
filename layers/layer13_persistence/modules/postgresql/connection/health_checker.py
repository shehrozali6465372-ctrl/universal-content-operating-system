"""DatabaseHealthChecker — Continuous health monitoring for PostgreSQL.

Monitors connection alive status, response time, pool stats,
and table health on a background thread.
"""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional


class DatabaseHealthChecker:
    """Background health monitor for database connection pool."""

    def __init__(self, pool: Any, interval_seconds: int = 30):
        self._pool = pool
        self._interval = interval_seconds
        self._history: List[Dict[str, Any]] = []
        self._max_history = 100
        self._monitoring = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def check(self) -> Dict[str, Any]:
        """Run a single health check and return results."""
        start = time.time()
        alive = False
        response_time_ms = 0.0

        try:
            self._pool.query_one("SELECT 1")
            alive = True
            response_time_ms = (time.time() - start) * 1000
        except Exception:
            response_time_ms = (time.time() - start) * 1000

        metrics = self._pool.get_pool_metrics() if hasattr(self._pool, 'get_pool_metrics') else {}

        # Table counts
        table_counts = {}
        try:
            tables = self._pool.get_tables()
            for t in tables:
                table_counts[t] = self._pool.count(t)
        except Exception:
            pass

        result = {
            "timestamp": time.time(),
            "connection_alive": alive,
            "response_time_ms": round(response_time_ms, 2),
            "pool_metrics": metrics,
            "table_counts": table_counts,
            "consecutive_failures": metrics.get("consecutive_failures", 0),
            "status": "healthy" if alive else "unhealthy",
        }

        with self._lock:
            self._history.append(result)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

        return result

    def start_monitoring(self) -> None:
        """Start background health monitoring thread."""
        if self._monitoring:
            return
        self._monitoring = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        self._monitoring = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    def _monitor_loop(self) -> None:
        """Background loop that runs health checks."""
        while self._monitoring:
            try:
                self.check()
            except Exception:
                pass
            time.sleep(self._interval)

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return last N health check results."""
        with self._lock:
            return list(self._history[-limit:])

    def get_summary(self) -> Dict[str, Any]:
        """Return a summary of all health checks."""
        with self._lock:
            if not self._history:
                return {"total_checks": 0, "status": "no_data"}
            alive_count = sum(1 for h in self._history if h["connection_alive"])
            avg_latency = sum(h["response_time_ms"] for h in self._history) / len(self._history)
            return {
                "total_checks": len(self._history),
                "alive_count": alive_count,
                "dead_count": len(self._history) - alive_count,
                "uptime_pct": round(alive_count / len(self._history) * 100, 1),
                "avg_latency_ms": round(avg_latency, 2),
                "last_check": self._history[-1]["status"],
            }
