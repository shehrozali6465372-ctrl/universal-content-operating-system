"""
Score Normalizer
Layer 2: Research Engine — Module 8

Normalizes scores from different modules to a common scale:
- Min-max normalization
- Z-score normalization
- Clipping
- Aggregation
"""

from typing import Dict, List


class ScoreNormalizer:
    """Normalize scores to 0-10 scale."""

    @staticmethod
    def normalize_minmax(value: float, min_val: float = 0.0, max_val: float = 10.0) -> float:
        """Normalize a value to 0-10 scale using min-max."""
        if max_val == min_val:
            return 5.0
        normalized = (value - min_val) / (max_val - min_val) * 10.0
        return round(max(0.0, min(10.0, normalized)), 2)

    @staticmethod
    def normalize_percentile(value: float, values: List[float]) -> float:
        """Normalize by percentile rank."""
        if not values:
            return 5.0
        below = sum(1 for v in values if v < value)
        return round(below / len(values) * 10, 2)

    @staticmethod
    def clip(value: float, low: float = 0.0, high: float = 10.0) -> float:
        return round(max(low, min(high, value)), 2)

    @staticmethod
    def normalize_distribution(values: Dict[str, float]) -> Dict[str, float]:
        """Normalize a set of values to 0-10 preserving relative ordering."""
        if not values:
            return {}
        vals = list(values.values())
        min_v = min(vals)
        max_v = max(vals)
        if max_v == min_v:
            return {k: 5.0 for k in values}
        return {
            k: round((v - min_v) / (max_v - min_v) * 10, 2)
            for k, v in values.items()
        }

    @staticmethod
    def weighted_average(scores: Dict[str, float], weights: Dict[str, float]) -> float:
        """Compute weighted average of scores."""
        total_weight = 0.0
        total_score = 0.0
        for key, score in scores.items():
            w = weights.get(key, 0.0)
            total_score += score * w
            total_weight += w
        return round(total_score / total_weight, 2) if total_weight > 0 else 0.0

    @staticmethod
    def geometric_mean(values: List[float]) -> float:
        """Geometric mean of positive values."""
        if not values or any(v <= 0 for v in values):
            return 0.0
        product = 1.0
        for v in values:
            product *= v
        return round(product ** (1.0 / len(values)), 2)

    @staticmethod
    def harmonic_mean(values: List[float]) -> float:
        """Harmonic mean of positive values."""
        if not values or any(v <= 0 for v in values):
            return 0.0
        reciprocal_sum = sum(1.0 / v for v in values)
        return round(len(values) / reciprocal_sum, 2)
