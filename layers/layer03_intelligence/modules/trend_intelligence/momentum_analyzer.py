"""Momentum Analyzer - Measures trend velocity and acceleration."""
from __future__ import annotations
from typing import Dict, List


class MomentumResult:
    """Result of momentum analysis."""
    __slots__ = ("velocity", "acceleration", "is_accelerating", "momentum_score",
                 "direction", "stability")

    def __init__(self) -> None:
        self.velocity = 0.0
        self.acceleration = 0.0
        self.is_accelerating = False
        self.momentum_score = 0.0
        self.direction = "stable"
        self.stability = 0.0

    def to_dict(self) -> Dict:
        return {
            "velocity": round(self.velocity, 4), "acceleration": round(self.acceleration, 4),
            "is_accelerating": self.is_accelerating, "momentum_score": round(self.momentum_score, 3),
            "direction": self.direction, "stability": round(self.stability, 3),
        }


class MomentumAnalyzer:
    """Analyzes velocity and acceleration of trend signals."""

    def analyze(self, data_points: List[float]) -> MomentumResult:
        result = MomentumResult()
        if len(data_points) < 2:
            return result

        diffs = [data_points[i + 1] - data_points[i] for i in range(len(data_points) - 1)]
        result.velocity = sum(diffs) / len(diffs) if diffs else 0.0

        if len(diffs) > 1:
            acc_diffs = [diffs[i + 1] - diffs[i] for i in range(len(diffs) - 1)]
            result.acceleration = sum(acc_diffs) / len(acc_diffs) if acc_diffs else 0.0

        result.is_accelerating = result.acceleration > 0

        max_val = max(abs(max(data_points, default=0)), abs(min(data_points, default=0)), 1)
        result.momentum_score = max(-1.0, min(1.0, (result.velocity + result.acceleration * 0.5) / max_val))

        if result.velocity > 0.05:
            result.direction = "rising"
        elif result.velocity < -0.05:
            result.direction = "falling"
        else:
            result.direction = "stable"

        if len(diffs) > 1:
            mean_diff = sum(diffs) / len(diffs)
            variance = sum((d - mean_diff) ** 2 for d in diffs) / len(diffs)
            result.stability = max(0.0, 1.0 - min(1.0, variance))
        else:
            result.stability = 0.5

        return result

    def analyze_with_timestamps(self, timestamped_data: List[Dict]) -> MomentumResult:
        if not timestamped_data:
            return MomentumResult()
        sorted_data = sorted(timestamped_data, key=lambda d: d.get("timestamp", 0))
        values = [d.get("score", d.get("value", 0)) for d in sorted_data]
        return self.analyze(values)
