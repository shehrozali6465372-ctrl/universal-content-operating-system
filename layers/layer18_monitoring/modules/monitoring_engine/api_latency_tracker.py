"""Thread-safe bounded API latency and error-rate tracking."""
from __future__ import annotations

import threading
import time
from typing import Any, Dict, List


class APILatencyTracker:
    def __init__(self, history_size: int = 10000) -> None:
        if history_size <= 0:
            raise ValueError("history_size must be positive")
        self._history_size = history_size
        self._lock = threading.RLock()
        self._endpoints: Dict[str, List[Dict[str, Any]]] = {}
        self._total_requests = 0
        self._total_errors = 0
        self._total_latency_ms = 0.0

    def record(self, endpoint: str, latency_ms: float, status_code: int = 200,
               method: str = "GET") -> None:
        if not endpoint.strip():
            raise ValueError("endpoint is required")
        if latency_ms < 0:
            raise ValueError("latency_ms cannot be negative")
        if not 100 <= status_code <= 599:
            raise ValueError("status_code must be a valid HTTP status code")
        now = time.time()
        entry = {"endpoint": endpoint, "latency_ms": round(float(latency_ms), 2),
                 "status_code": status_code, "method": method.upper(), "timestamp": now,
                 "is_error": status_code >= 400}
        with self._lock:
            history = self._endpoints.setdefault(endpoint, [])
            history.append(entry)
            if len(history) > self._history_size:
                del history[:-self._history_size]
            self._total_requests += 1
            self._total_latency_ms += float(latency_ms)
            if status_code >= 400:
                self._total_errors += 1

    def get_endpoint_stats(self, endpoint: str) -> Dict[str, Any]:
        with self._lock:
            entries = list(self._endpoints.get(endpoint, []))
        if not entries:
            return {"endpoint": endpoint, "requests": 0}
        latencies = [e["latency_ms"] for e in entries]
        errors = sum(e["is_error"] for e in entries)
        return self._compute_stats(endpoint, latencies, errors, len(entries))

    def get_all_stats(self) -> Dict[str, Any]:
        with self._lock:
            endpoints = list(self._endpoints)
        return {endpoint: self.get_endpoint_stats(endpoint) for endpoint in endpoints}

    def get_slow_endpoints(self, threshold_ms: float = 1000, top_k: int = 10) -> List[Dict[str, Any]]:
        if threshold_ms < 0 or top_k <= 0:
            raise ValueError("threshold_ms must be non-negative and top_k positive")
        slow = [{"endpoint": endpoint, **stats} for endpoint, stats in self.get_all_stats().items()
                if stats.get("p95_ms", 0) >= threshold_ms]
        slow.sort(key=lambda item: (-item["p95_ms"], item["endpoint"]))
        return slow[:top_k]

    def get_throughput(self, window_seconds: float = 60) -> Dict[str, Any]:
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        cutoff = time.time() - window_seconds
        with self._lock:
            total = sum(1 for entries in self._endpoints.values()
                        for entry in entries if entry["timestamp"] >= cutoff)
        return {"requests_in_window": total, "window_seconds": window_seconds,
                "requests_per_second": round(total / window_seconds, 2)}

    def get_error_rate(self, window_seconds: float = 300) -> Dict[str, Any]:
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        cutoff = time.time() - window_seconds
        with self._lock:
            entries = [entry for values in self._endpoints.values() for entry in values
                       if entry["timestamp"] >= cutoff]
        total = len(entries)
        errors = sum(e["is_error"] for e in entries)
        return {"total": total, "errors": errors,
                "error_rate_pct": round(errors / total * 100, 2) if total else 0.0}

    @staticmethod
    def _compute_stats(endpoint: str, latencies: List[float], errors: int, total: int) -> Dict[str, Any]:
        values = sorted(latencies)
        n = len(values)
        def percentile(q: float) -> float:
            return values[min(n - 1, int((n - 1) * q))]
        return {"endpoint": endpoint, "requests": total, "avg_ms": round(sum(values) / n, 2),
                "min_ms": values[0], "max_ms": values[-1],
                "p50_ms": percentile(.50), "p95_ms": percentile(.95), "p99_ms": percentile(.99),
                "errors": errors, "error_rate_pct": round(errors / total * 100, 2)}

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {"total_requests": self._total_requests, "total_errors": self._total_errors,
                    "total_latency_ms": round(self._total_latency_ms, 2),
                    "avg_latency_ms": round(self._total_latency_ms / self._total_requests, 2)
                    if self._total_requests else 0.0,
                    "error_rate_pct": round(self._total_errors / self._total_requests * 100, 2)
                    if self._total_requests else 0.0,
                    "tracked_endpoints": len(self._endpoints)}
