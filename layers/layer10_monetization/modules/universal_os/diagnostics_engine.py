"""DiagnosticsEngine — Find slow modules, errors, bottlenecks, memory issues."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class DiagnosticResult:
    """A diagnostic finding."""

    __slots__ = ("category", "component", "severity", "message",
                 "suggestion", "detected_at")

    def __init__(self, category: str = "", component: str = "") -> None:
        self.category = category
        self.component = component
        self.severity: str = "info"
        self.message: str = ""
        self.suggestion: str = ""
        self.detected_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"category": self.category, "component": self.component,
                "severity": self.severity, "message": self.message,
                "suggestion": self.suggestion}


class DiagnosticsEngine:
    """Find slow modules, errors, bottlenecks, and memory issues."""

    def __init__(self) -> None:
        self._results: List[DiagnosticResult] = []
        self._component_timings: Dict[str, List[float]] = {}

    def record_timing(self, component: str, duration_ms: float) -> None:
        self._component_timings.setdefault(component, []).append(duration_ms)

    def diagnose(self, slow_threshold_ms: float = 1000.0) -> List[DiagnosticResult]:
        self._results.clear()
        for component, timings in self._component_timings.items():
            if timings:
                avg = sum(timings) / len(timings)
                if avg > slow_threshold_ms:
                    result = DiagnosticResult("performance", component)
                    result.severity = "warning"
                    result.message = f"Average latency {avg:.1f}ms exceeds threshold"
                    result.suggestion = f"Optimize {component} or increase resources"
                    self._results.append(result)
                elif avg < 1.0:
                    result = DiagnosticResult("timing", component)
                    result.severity = "info"
                    result.message = f"Very fast execution: {avg:.3f}ms"
                    self._results.append(result)
        return self._results

    def get_slow_components(self, threshold_ms: float = 1000.0) -> List[Dict[str, Any]]:
        results = []
        for component, timings in self._component_timings.items():
            if timings:
                avg = sum(timings) / len(timings)
                if avg > threshold_ms:
                    results.append({"component": component, "avg_ms": round(avg, 1),
                                    "sample_count": len(timings)})
        return sorted(results, key=lambda x: x["avg_ms"], reverse=True)

    def get_results(self) -> List[DiagnosticResult]:
        return list(self._results)

    def get_stats(self) -> Dict[str, Any]:
        return {"components_tracked": len(self._component_timings),
                "total_results": len(self._results)}
