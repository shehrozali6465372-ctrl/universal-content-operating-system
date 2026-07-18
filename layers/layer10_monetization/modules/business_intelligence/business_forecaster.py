"""BusinessForecaster — Predict revenue, expenses, and growth."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_BF_COUNTER = itertools.count(1)


class ForecastResult:
    """A business forecast result."""

    __slots__ = ("forecast_id", "forecast_type", "metric", "predicted_value",
                 "confidence", "period", "factors", "created_at")

    def __init__(self, forecast_type: str = "", metric: str = "") -> None:
        self.forecast_id: str = f"fcst_{next(_BF_COUNTER)}"
        self.forecast_type = forecast_type
        self.metric = metric
        self.predicted_value: float = 0.0
        self.confidence: float = 0.5
        self.period: str = ""
        self.factors: List[str] = []
        self.created_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"forecast_id": self.forecast_id, "type": self.forecast_type,
                "metric": self.metric, "predicted_value": round(self.predicted_value, 2),
                "confidence": round(self.confidence, 3), "period": self.period}


class BusinessForecaster:
    """Forecast revenue, expenses, profit, growth, and market opportunities."""

    def __init__(self) -> None:
        self._forecasts: List[ForecastResult] = []
        self._historical: Dict[str, List[float]] = {}

    def forecast(self, forecast_type: str, metric: str, period: str,
                 historical_values: List[float] = None,
                 factors: List[str] = None) -> ForecastResult:
        result = ForecastResult(forecast_type, metric)
        result.period = period
        if factors:
            result.factors = list(factors)
        values = historical_values or self._historical.get(metric, [])
        if len(values) >= 2:
            recent = values[-3:] if len(values) >= 3 else values
            growth = (recent[-1] - recent[0]) / max(1, abs(recent[0]))
            result.predicted_value = round(recent[-1] * (1 + growth), 2)
            result.confidence = min(0.9, 0.3 + len(values) * 0.05)
        elif len(values) == 1:
            result.predicted_value = values[0]
            result.confidence = 0.2
        self._forecasts.append(result)
        self._historical.setdefault(metric, []).extend(values)
        return result

    def forecast_revenue(self, period: str, current_revenue: float,
                         growth_rate: float = 0.0) -> ForecastResult:
        predicted = current_revenue * (1 + growth_rate)
        result = self.forecast("revenue", "revenue", period,
                               [current_revenue])
        result.predicted_value = round(predicted, 2)
        result.factors = [f"growth_rate={growth_rate}"]
        result.confidence = min(0.8, 0.3 + abs(growth_rate) * 2)
        return result

    def forecast_growth(self, period: str, metric: str,
                        values: List[float]) -> ForecastResult:
        return self.forecast("growth", metric, period, values)

    def get_forecasts(self, forecast_type: str = "",
                      metric: str = "") -> List[ForecastResult]:
        results = self._forecasts
        if forecast_type:
            results = [f for f in results if f.forecast_type == forecast_type]
        if metric:
            results = [f for f in results if f.metric == metric]
        return results

    def get_latest_forecast(self, metric: str = "") -> ForecastResult:
        forecasts = self._forecasts
        if metric:
            forecasts = [f for f in forecasts if f.metric == metric]
        return forecasts[-1] if forecasts else None

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for f in self._forecasts:
            types[f.forecast_type] = types.get(f.forecast_type, 0) + 1
        return {"total_forecasts": len(self._forecasts), "by_type": types}
