"""Performance Optimizer — Optimize system performance."""
from __future__ import annotations
from typing import Any, Dict, List


class PerformanceOptimizer:
    """Optimize latency, resource usage, and throughput."""

    def __init__(self) -> None:
        self._metrics: Dict[str, List[float]] = {
            "latency_ms": [], "cpu_usage": [], "memory_usage": [],
            "api_calls": [], "queue_depth": [],
        }
        self._optimizations: List[Dict[str, Any]] = []

    def record_metric(self, metric: str, value: float) -> None:
        if metric not in self._metrics:
            self._metrics[metric] = []
        self._metrics[metric].append(value)

    def get_average(self, metric: str) -> float:
        values = self._metrics.get(metric, [])
        if not values:
            return 0.0
        return round(sum(values) / len(values), 3)

    def analyze(self) -> Dict[str, Any]:
        analysis = {}
        for metric, values in self._metrics.items():
            if values:
                analysis[metric] = {
                    "avg": round(sum(values) / len(values), 3),
                    "max": round(max(values), 3),
                    "min": round(min(values), 3),
                    "samples": len(values),
                }
        return analysis

    def suggest_optimizations(self) -> List[Dict[str, Any]]:
        suggestions = []
        latency = self.get_average("latency_ms")
        if latency > 1000:
            suggestions.append({"type": "latency", "suggestion": "Reduce batch size", "priority": "high"})
        cpu = self.get_average("cpu_usage")
        if cpu > 0.8:
            suggestions.append({"type": "cpu", "suggestion": "Scale workers", "priority": "high"})
        queue = self.get_average("queue_depth")
        if queue > 50:
            suggestions.append({"type": "queue", "suggestion": "Add consumers", "priority": "medium"})
        self._optimizations.extend(suggestions)
        return suggestions

    def get_stats(self) -> Dict[str, Any]:
        return {
            "metrics_tracked": len(self._metrics),
            "total_optimizations": len(self._optimizations),
            "analysis": self.analyze(),
        }
