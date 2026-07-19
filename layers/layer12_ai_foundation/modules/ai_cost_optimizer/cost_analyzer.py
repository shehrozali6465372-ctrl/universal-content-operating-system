"""CostAnalyzer — analyze cost patterns and detect anomalies."""
from __future__ import annotations
from typing import Any, Dict, List

class CostAnalyzer:
    def __init__(self) -> None:
        self._analysis_cache: Dict[str, Any] = {}
    def analyze(self, costs: List[float]) -> Dict[str, Any]:
        if not costs: return {"count": 0, "avg": 0.0}
        avg = sum(costs) / len(costs)
        variance = sum((c - avg) ** 2 for c in costs) / len(costs)
        return {"count": len(costs), "avg": round(avg, 6), "min": min(costs),
                "max": max(costs), "variance": round(variance, 8)}
    def detect_anomalies(self, costs: List[float], threshold: float = 2.0) -> List[int]:
        if len(costs) < 3: return []
        avg = sum(costs) / len(costs)
        std = (sum((c - avg) ** 2 for c in costs) / len(costs)) ** 0.5
        if std == 0: return []
        return [i for i, c in enumerate(costs) if abs(c - avg) / std > threshold]
