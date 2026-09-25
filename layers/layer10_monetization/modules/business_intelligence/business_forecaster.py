"""BusinessForecaster — bounded, explicitly parameterized forecasts."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_BF_COUNTER = itertools.count(1)


class ForecastResult:
    def __init__(self, forecast_type: str = "", metric: str = "") -> None:
        self.forecast_id = f"fcst_{next(_BF_COUNTER)}"
        self.forecast_type, self.metric = forecast_type, metric
        self.predicted_value = 0.0
        self.confidence = 0.0
        self.period = ""
        self.factors: List[str] = []
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"forecast_id": self.forecast_id, "type": self.forecast_type,
                "metric": self.metric, "predicted_value": round(self.predicted_value, 2),
                "confidence": round(self.confidence, 3), "period": self.period}


class BusinessForecaster:
    def __init__(self, max_history: int = 10000, max_forecasts: int = 10000) -> None:
        if max_history <= 0 or max_forecasts <= 0:
            raise ValueError("history limits must be positive")
        self._max_history, self._max_forecasts = max_history, max_forecasts
        self._forecasts: List[ForecastResult] = []
        self._historical: Dict[str, List[float]] = {}

    def forecast(self, forecast_type: str, metric: str, period: str,
                 historical_values: Optional[List[float]] = None,
                 factors: Optional[List[str]] = None) -> ForecastResult:
        values = list(historical_values) if historical_values is not None else list(self._historical.get(metric, []))
        if any(value < 0 for value in values):
            raise ValueError("historical values must be non-negative")
        result = ForecastResult(forecast_type, metric)
        result.period = period
        result.factors = list(factors or [])
        if len(values) >= 2:
            recent = values[-3:]
            if recent[0] == 0:
                result.predicted_value = recent[-1]
            else:
                growth = (recent[-1] - recent[0]) / abs(recent[0])
                result.predicted_value = max(0.0, recent[-1] * (1 + growth))
            result.confidence = min(0.9, 0.3 + len(values) * 0.05)
        elif len(values) == 1:
            result.predicted_value = values[0]
            result.confidence = 0.2
        self._forecasts.append(result)
        history = self._historical.setdefault(metric, [])
        history.extend(values)
        if len(history) > self._max_history:
            del history[:-self._max_history]
        if len(self._forecasts) > self._max_forecasts:
            del self._forecasts[:-self._max_forecasts]
        return result

    def forecast_revenue(self, period: str, current_revenue: float,
                         growth_rate: float = 0.0) -> ForecastResult:
        if current_revenue < 0 or growth_rate < -1:
            raise ValueError("invalid revenue or growth rate")
        result = self.forecast("revenue", "revenue", period, [current_revenue],
                               [f"growth_rate={growth_rate}"])
        result.predicted_value = round(current_revenue * (1 + growth_rate), 2)
        result.confidence = 0.0 if growth_rate != 0 else 0.2
        return result

    def forecast_growth(self, period: str, metric: str, values: List[float]) -> ForecastResult:
        return self.forecast("growth", metric, period, values)

    def get_forecasts(self, forecast_type: str = "", metric: str = "") -> List[ForecastResult]:
        return [f for f in self._forecasts
                if (not forecast_type or f.forecast_type == forecast_type)
                and (not metric or f.metric == metric)]

    def get_latest_forecast(self, metric: str = "") -> Optional[ForecastResult]:
        forecasts = self.get_forecasts(metric=metric)
        return forecasts[-1] if forecasts else None

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for forecast in self._forecasts:
            types[forecast.forecast_type] = types.get(forecast.forecast_type, 0) + 1
        return {"total_forecasts": len(self._forecasts), "by_type": types}
