"""APILatencyTracker — Track API request/response timing.

Features:
- Per-endpoint latency tracking
- Percentile calculations (p50, p95, p99)
- Throughput tracking (requests per second)
- Error rate tracking
- Time-windowed analysis
- Slow endpoint detection
"""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional


class APILatencyTracker:
    """Track API latency and throughput."""

    def __init__(self, history_size: int = 10000):
        self._history_size = history_size
        self._lock = threading.Lock()

        # Per-endpoint data
        self._endpoints: Dict[str, List[Dict[str, Any]]] = {}

        # Global counters
        self._total_requests = 0
        self._total_errors = 0
        self._total_latency_ms = 0.0

    def record(self, endpoint: str, latency_ms: float, status_code: int = 200,
               method: str = "GET") -> None:
        """Record an API request.

        Args:
            endpoint: API endpoint path
            latency_ms: Response time in milliseconds
            status_code: HTTP status code
            method: HTTP method
        """
        now = time.time()
        entry = {
            "endpoint": endpoint,
            "latency_ms": round(latency_ms, 2),
            "status_code": status_code,
            "method": method,
            "timestamp": now,
            "is_error": status_code >= 400,
        }

        with self._lock:
            if endpoint not in self._endpoints:
                self._endpoints[endpoint] = []
            self._endpoints[endpoint].append(entry)

            # Trim
            if len(self._endpoints[endpoint]) > self._history_size:
                self._endpoints[endpoint] = self._endpoints[endpoint][-self._history_size:]

            self._total_requests += 1
            self._total_latency_ms += latency_ms
            if status_code >= 400:
                self._total_errors += 1

    def get_endpoint_stats(self, endpoint: str) -> Dict[str, Any]:
        """Get statistics for a specific endpoint."""
        with self._lock:
            entries = self._endpoints.get(endpoint, [])

        if not entries:
            return {"endpoint": endpoint, "requests": 0}

        latencies = [e["latency_ms"] for e in entries]
        errors = sum(1 for e in entries if e["is_error"])

        return self._compute_stats(endpoint, latencies, errors, len(entries))

    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all endpoints."""
        with self._lock:
            endpoints = list(self._endpoints.keys())

        return {ep: self.get_endpoint_stats(ep) for ep in endpoints}

    def get_slow_endpoints(self, threshold_ms: float = 1000, top_k: int = 10) -> List[Dict[str, Any]]:
        """Find endpoints with high latency."""
        all_stats = self.get_all_stats()
        slow = []
        for ep, stats in all_stats.items():
            if stats.get("p95_ms", 0) >= threshold_ms:
                slow.append({"endpoint": ep, **stats})
        slow.sort(key=lambda x: x.get("p95_ms", 0), reverse=True)
        return slow[:top_k]

    def get_throughput(self, window_seconds: float = 60) -> Dict[str, Any]:
        """Get requests per second in a time window."""
        now = time.time()
        cutoff = now - window_seconds
        total = 0

        with self._lock:
            for entries in self._endpoints.values():
                for e in entries:
                    if e["timestamp"] >= cutoff:
                        total += 1

        rps = total / window_seconds if window_seconds > 0 else 0
        return {"requests_in_window": total, "window_seconds": window_seconds,
                "requests_per_second": round(rps, 2)}

    def get_error_rate(self, window_seconds: float = 300) -> Dict[str, Any]:
        """Get error rate in a time window."""
        now = time.time()
        cutoff = now - window_seconds
        total = 0
        errors = 0

        with self._lock:
            for entries in self._endpoints.values():
                for e in entries:
                    if e["timestamp"] >= cutoff:
                        total += 1
                        if e["is_error"]:
                            errors += 1

        rate = errors / total * 100 if total > 0 else 0
        return {"total": total, "errors": errors, "error_rate_pct": round(rate, 2)}

    def _compute_stats(self, endpoint: str, latencies: List[float],
                       errors: int, total: int) -> Dict[str, Any]:
        """Compute latency statistics."""
        sorted_lats = sorted(latencies)
        n = len(sorted_lats)
        avg = sum(sorted_lats) / n
        p50 = sorted_lats[int(n * 0.5)] if n >= 2 else sorted_lats[-1]
        p95 = sorted_lats[int(n * 0.95)] if n >= 2 else sorted_lats[-1]
        p99 = sorted_lats[int(n * 0.99)] if n >= 2 else sorted_lats[-1]

        return {
            "endpoint": endpoint,
            "requests": total,
            "avg_ms": round(avg, 2),
            "min_ms": round(sorted_lats[0], 2),
            "max_ms": round(sorted_lats[-1], 2),
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2),
            "errors": errors,
            "error_rate_pct": round(errors / total * 100, 2) if total > 0 else 0,
        }

    def stats(self) -> Dict[str, Any]:
        """Get global statistics."""
        return {
            "total_requests": self._total_requests,
            "total_errors": self._total_errors,
            "total_latency_ms": round(self._total_latency_ms, 2),
            "avg_latency_ms": round(
                self._total_latency_ms / self._total_requests, 2
            ) if self._total_requests > 0 else 0,
            "error_rate_pct": round(
                self._total_errors / self._total_requests * 100, 2
            ) if self._total_requests > 0 else 0,
            "tracked_endpoints": len(self._endpoints),
        }
