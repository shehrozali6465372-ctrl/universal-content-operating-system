"""Seasonality Analyzer — Detects periodic patterns in trend data."""
from __future__ import annotations
from typing import Dict, List, Optional


class SeasonalPattern:
    """Detected seasonal pattern for a trend."""
    __slots__ = ("topic", "period_days", "amplitude", "phase", "strength",
                 "peak_months", "pattern_type")

    def __init__(self, topic: str = "", period_days: int = 0, amplitude: float = 0.0,
                 phase: float = 0.0, strength: float = 0.0,
                 peak_months: Optional[List[int]] = None, pattern_type: str = "unknown"):
        self.topic = topic
        self.period_days = period_days
        self.amplitude = amplitude
        self.phase = phase
        self.strength = strength
        self.peak_months = peak_months or []
        self.pattern_type = pattern_type  # weekly, monthly, yearly, none

    def to_dict(self) -> Dict:
        return {
            "topic": self.topic, "period_days": self.period_days,
            "amplitude": round(self.amplitude, 3), "phase": round(self.phase, 3),
            "strength": round(self.strength, 3), "peak_months": self.peak_months,
            "pattern_type": self.pattern_type,
        }


class SeasonalityAnalyzer:
    """Detects seasonality in time-series trend data."""

    KNOWN_PERIODS = {
        "weekly": 7, "monthly": 30, "quarterly": 91, "yearly": 365,
    }

    def detect(self, topic: str, data_points: List[Dict[str, float]]) -> SeasonalPattern:
        """Detect seasonal patterns in time-series data.

        Args:
            topic: The trend topic
            data_points: List of {"timestamp": float, "score": float}
        """
        if len(data_points) < 14:
            return SeasonalPattern(topic, pattern_type="insufficient_data")

        scores = [d["score"] for d in data_points]
        timestamps = [d["timestamp"] for d in data_points]

        mean_score = sum(scores) / len(scores)
        if mean_score == 0:
            return SeasonalPattern(topic, pattern_type="no_signal")

        best_period = 0
        best_strength = 0.0

        for name, period in self.KNOWN_PERIODS.items():
            strength = self._autocorrelation(scores, period)
            if strength > best_strength:
                best_strength = strength
                best_period = period

        if best_strength < 0.2:
            return SeasonalPattern(topic, pattern_type="none", strength=best_strength)

        amplitude = max(scores) - min(scores)
        phase = self._estimate_phase(scores, best_period)

        return SeasonalPattern(
            topic=topic, period_days=best_period, amplitude=amplitude,
            phase=phase, strength=round(best_strength, 3),
            pattern_type=self._period_name(best_period),
        )

    def _autocorrelation(self, values: List[float], lag: int) -> float:
        if lag >= len(values) // 2:
            return 0.0
        n = len(values) - lag
        mean = sum(values) / len(values)
        num = sum((values[i] - mean) * (values[i + lag] - mean) for i in range(n))
        den = sum((v - mean) ** 2 for v in values)
        return abs(num / den) if den > 0 else 0.0

    def _estimate_phase(self, values: List[float], period: int) -> float:
        if period <= 0:
            return 0.0
        max_idx = max(range(len(values)), key=lambda i: values[i])
        return (max_idx % period) / period

    def _period_name(self, period: int) -> str:
        for name, p in self.KNOWN_PERIODS.items():
            if p == period:
                return name
        return "custom"

    def predict_next_peak(self, pattern: SeasonalPattern, current_idx: int) -> int:
        if pattern.period_days <= 0:
            return -1
        return current_idx + pattern.period_days
