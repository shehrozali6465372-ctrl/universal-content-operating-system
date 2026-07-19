"""AIAnalyzer — analyze orchestrator performance."""
from __future__ import annotations
from typing import Any, Dict, List

class AIAnalyzer:
    def __init__(self) -> None:
        self._analyses: List[Dict[str, Any]] = []
    def analyze(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        issues: List[str] = []
        if metrics.get("success_rate", 1.0) < 0.8: issues.append("Low success rate")
        if metrics.get("avg_latency_ms", 0) > 5000: issues.append("High latency")
        result = {"issues": issues, "healthy": len(issues) == 0,
                  "score": max(0.0, 1.0 - len(issues) * 0.3)}
        self._analyses.append(result); return result
    def get_history(self) -> List[Dict[str, Any]]: return list(self._analyses)
