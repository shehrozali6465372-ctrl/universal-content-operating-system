"""CostForecaster — predict future costs."""
from __future__ import annotations
from typing import Any, Dict, List

class CostForecaster:
    def __init__(self) -> None:
        self._forecasts: List[Dict[str, Any]] = []
    def predict(self, history: List[float], days_ahead: int = 7) -> Dict[str, Any]:
        if not history:
            avg = 0.0
        else:
            avg = sum(history) / len(history)
        projected = avg * days_ahead
        result = {"avg_daily": avg, "projected_days": days_ahead,
                  "projected_total": projected, "confidence": min(0.9, 0.3 + len(history) * 0.05)}
        self._forecasts.append(result)
        return result
    def predict_monthly(self, daily_costs: List[float]) -> float:
        avg = sum(daily_costs) / max(len(daily_costs), 1)
        return avg * 30
    def get_history(self) -> list:
        return list(self._forecasts)
