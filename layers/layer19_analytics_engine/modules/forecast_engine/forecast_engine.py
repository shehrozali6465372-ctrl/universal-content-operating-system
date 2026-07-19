"""ForecastEngine — simple forecasting algorithms."""
from __future__ import annotations
import math
from typing import Any, Dict, List, Optional


class ForecastResult:
    __slots__ = ("series_name", "predictions", "method", "confidence", "metadata")

    def __init__(self, series_name: str, predictions: List[float],
                 method: str = "moving_average", confidence: float = 0.8) -> None:
        self.series_name = series_name
        self.predictions = predictions
        self.method = method
        self.confidence = confidence
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"series": self.series_name, "predictions": self.predictions,
                "method": self.method, "confidence": self.confidence}


class ForecastEngine:
    def __init__(self) -> None:
        self._series: Dict[str, List[float]] = {}

    def add_data(self, series_name: str, values: List[float]) -> None:
        self._series.setdefault(series_name, []).extend(values)

    def moving_average_forecast(self, series_name: str, periods: int = 3,
                                window: int = 3) -> ForecastResult:
        data = self._series.get(series_name, [])
        if not data:
            return ForecastResult(series_name, [0.0] * periods, "moving_average", 0.0)
        predictions = []
        recent = list(data)
        for _ in range(periods):
            avg = sum(recent[-window:]) / min(window, len(recent))
            predictions.append(round(avg, 4))
            recent.append(avg)
        return ForecastResult(series_name, predictions, "moving_average", 0.7)

    def linear_forecast(self, series_name: str, periods: int = 3) -> ForecastResult:
        data = self._series.get(series_name, [])
        if len(data) < 2:
            return ForecastResult(series_name, [0.0] * periods, "linear", 0.0)
        n = len(data)
        x_mean = (n - 1) / 2
        y_mean = sum(data) / n
        num = sum((i - x_mean) * (data[i] - y_mean) for i in range(n))
        den = sum((i - x_mean) ** 2 for i in range(n))
        slope = num / den if den != 0 else 0
        intercept = y_mean - slope * x_mean
        predictions = [round(intercept + slope * (n + i), 4) for i in range(periods)]
        return ForecastResult(series_name, predictions, "linear", 0.6)

    def exponential_smoothing(self, series_name: str, periods: int = 3,
                              alpha: float = 0.3) -> ForecastResult:
        data = self._series.get(series_name, [])
        if not data:
            return ForecastResult(series_name, [0.0] * periods, "exponential_smoothing", 0.0)
        smoothed = data[0]
        for v in data[1:]:
            smoothed = alpha * v + (1 - alpha) * smoothed
        predictions = [round(smoothed, 4)] * periods
        return ForecastResult(series_name, predictions, "exponential_smoothing", 0.65)

    def list_series(self) -> List[str]:
        return list(self._series.keys())
