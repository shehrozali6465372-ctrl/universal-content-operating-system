"""Momentum Analyzer — measures trend velocity and acceleration."""

from typing import List


class MomentumResult:
    __slots__ = ("velocity", "acceleration", "is_accelerating", "momentum_score")

    def __init__(self):
        self.velocity = 0.0
        self.acceleration = 0.0
        self.is_accelerating = False
        self.momentum_score = 0.0

    def to_dict(self) -> dict:
        return {"velocity": self.velocity, "acceleration": self.acceleration,
                "is_accelerating": self.is_accelerating, "momentum_score": self.momentum_score}


class MomentumAnalyzer:
    def analyze(self, scores: List[float]) -> MomentumResult:
        result = MomentumResult()
        if len(scores) < 2:
            return result

        # Velocity: average rate of change
        diffs = [scores[i+1] - scores[i] for i in range(len(scores)-1)]
        result.velocity = round(sum(diffs) / len(diffs), 3)

        # Acceleration: rate of change of velocity
        if len(diffs) >= 2:
            accel_diffs = [diffs[i+1] - diffs[i] for i in range(len(diffs)-1)]
            result.acceleration = round(sum(accel_diffs) / len(accel_diffs), 3)
            result.is_accelerating = result.acceleration > 0

        # Momentum score (0-100)
        result.momentum_score = round(max(0, min(100, 50 + result.velocity * 5 + result.acceleration * 2)), 2)
        return result
