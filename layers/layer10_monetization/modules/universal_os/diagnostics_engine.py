"""DiagnosticsEngine — bounded timing diagnostics."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class DiagnosticResult:
    def __init__(self, category: str = "", component: str = "") -> None:
        self.category = category
        self.component = component
        self.severity = "info"
        self.message = ""
        self.suggestion = ""
        self.detected_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"category": self.category, "component": self.component,
                "severity": self.severity, "message": self.message,
                "suggestion": self.suggestion}


class DiagnosticsEngine:
    def __init__(self, max_samples: int = 1000) -> None:
        if max_samples <= 0:
            raise ValueError("max_samples must be positive")
        self._max_samples = max_samples
        self._results: List[DiagnosticResult] = []
        self._component_timings: Dict[str, List[float]] = {}

    def record_timing(self, component: str, duration_ms: float) -> None:
        if not component or duration_ms < 0:
            raise ValueError("component and non-negative duration are required")
        timings = self._component_timings.setdefault(component, [])
        timings.append(duration_ms)
        if len(timings) > self._max_samples:
            del timings[:-self._max_samples]

    def diagnose(self, slow_threshold_ms: float = 1000.0) -> List[DiagnosticResult]:
        if slow_threshold_ms < 0:
            raise ValueError("threshold must be non-negative")
        self._results.clear()
        for component, timings in self._component_timings.items():
            avg = sum(timings) / len(timings)
            if avg > slow_threshold_ms:
                result = DiagnosticResult("performance", component)
                result.severity = "warning"
                result.message = f"Average latency {avg:.1f}ms exceeds threshold"
                result.suggestion = f"Optimize {component} or increase resources"
                self._results.append(result)
            elif avg < 1.0:
                result = DiagnosticResult("timing", component)
                result.message = f"Very fast execution: {avg:.3f}ms"
                self._results.append(result)
        return list(self._results)

    def get_slow_components(self, threshold_ms: float = 1000.0) -> List[Dict[str, Any]]:
        results = []
        for component, timings in self._component_timings.items():
            avg = sum(timings) / len(timings)
            if avg > threshold_ms:
                results.append({"component": component, "avg_ms": round(avg, 1),
                                "sample_count": len(timings)})
        return sorted(results, key=lambda item: item["avg_ms"], reverse=True)

    def get_results(self) -> List[DiagnosticResult]:
        return list(self._results)

    def get_stats(self) -> Dict[str, Any]:
        return {"components_tracked": len(self._component_timings),
                "total_results": len(self._results)}
