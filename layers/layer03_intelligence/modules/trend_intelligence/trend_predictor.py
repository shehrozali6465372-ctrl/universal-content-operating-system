"""Trend Predictor - Predicts future trend trajectory from historical data."""
from __future__ import annotations
import math
from typing import Dict, List


class TrendPrediction:
    """Prediction for a trend future trajectory."""
    __slots__ = ("topic", "predicted_direction", "predicted_score", "confidence",
                 "timeframe_days", "trend_line_slope")

    def __init__(self, topic: str = "") -> None:
        self.topic = topic
        self.predicted_direction = "stable"
        self.predicted_score = 0.0
        self.confidence = 0.0
        self.timeframe_days = 7
        self.trend_line_slope = 0.0

    def to_dict(self) -> Dict:
        return {
            "topic": self.topic, "predicted_direction": self.predicted_direction,
            "predicted_score": round(self.predicted_score, 3),
            "confidence": round(self.confidence, 3),
            "timeframe_days": self.timeframe_days,
            "trend_line_slope": round(self.trend_line_slope, 4),
        }


class TrendPredictor:
    """Predicts trend trajectory using linear regression."""

    def predict(self, topic: str, history: List[float], timeframe_days: int = 7) -> TrendPrediction:
        result = TrendPrediction(topic)
        result.timeframe_days = timeframe_days

        if len(history) < 3:
            return result

        n = len(history)
        x_mean = (n - 1) / 2
        y_mean = sum(history) / n
        num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(history))
        den = sum((i - x_mean) ** 2 for i in range(n))
        slope = num / den if den > 0 else 0.0
        intercept = y_mean - slope * x_mean

        result.trend_line_slope = slope
        result.predicted_score = max(0, intercept + slope * (n - 1 + timeframe_days))

        if slope > 0.05:
            result.predicted_direction = "rising"
        elif slope < -0.05:
            result.predicted_direction = "falling"
        else:
            result.predicted_direction = "stable"

        ss_res = sum((history[i] - (intercept + slope * i)) ** 2 for i in range(n))
        ss_tot = sum((v - y_mean) ** 2 for v in history)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        result.confidence = max(0.0, min(1.0, r_squared))

        return result

    def predict_with_decay(self, topic: str, history: List[float],
                           decay_rate: float = 0.1, timeframe_days: int = 7) -> TrendPrediction:
        result = self.predict(topic, history, timeframe_days)
        decay_factor = math.exp(-decay_rate * timeframe_days)
        result.predicted_score *= decay_factor
        if result.predicted_score < history[-1] * 0.5:
            result.predicted_direction = "declining"
        result.confidence *= decay_factor
        return result
