"""Signal Normalizer - Normalizes raw signals to 0-1 scale."""
from __future__ import annotations
from typing import Dict, List
import statistics


class NormalizedSignal:
    __slots__ = ("signal_type", "raw_value", "normalized_value", "method", "percentile")
    def __init__(self, signal_type: str = "", raw_value: float = 0.0, normalized: float = 0.0):
        self.signal_type = signal_type
        self.raw_value = raw_value
        self.normalized_value = normalized
        self.method = "min_max"
        self.percentile = 0.0
    def to_dict(self) -> Dict:
        return {"type": self.signal_type, "raw": round(self.raw_value, 4),
                "normalized": round(self.normalized_value, 3), "method": self.method}


class SignalNormalizer:
    """Normalizes signals using min-max or z-score methods."""
    def __init__(self, method: str = "min_max") -> None:
        self._method = method
        self._history: Dict[str, List[float]] = {}

    def normalize(self, signal_type: str, value: float) -> NormalizedSignal:
        if signal_type not in self._history:
            self._history[signal_type] = []
        self._history[signal_type].append(value)

        values = self._history[signal_type]
        result = NormalizedSignal(signal_type, value)
        result.method = self._method

        if self._method == "min_max" and len(values) >= 2:
            mn, mx = min(values), max(values)
            rng = mx - mn
            result.normalized_value = (value - mn) / rng if rng > 0 else 0.5
        elif self._method == "z_score" and len(values) >= 3:
            mean = statistics.mean(values)
            stdev = statistics.stdev(values) or 1.0
            result.normalized_value = max(0.0, min(1.0, (value - mean) / (stdev * 3) + 0.5))
        else:
            result.normalized_value = min(1.0, max(0.0, value))

        # Percentile
        below = sum(1 for v in values if v <= value)
        result.percentile = below / len(values)
        return result

    def normalize_batch(self, signals: List[Dict]) -> List[NormalizedSignal]:
        return [self.normalize(s.get("type", ""), s.get("value", 0)) for s in signals]
