"""StatisticsEngine — descriptive and inferential statistics."""
from __future__ import annotations
import math
from typing import Any, Dict, List, Optional


class StatisticsEngine:
    def __init__(self) -> None:
        self._datasets: Dict[str, List[float]] = {}

    def add_dataset(self, name: str, values: List[float]) -> None:
        self._datasets[name] = list(values)

    def describe(self, name: str) -> Dict[str, float]:
        data = self._datasets.get(name, [])
        if not data:
            return {"count": 0}
        n = len(data)
        mean = sum(data) / n
        variance = sum((x - mean) ** 2 for x in data) / max(n - 1, 1)
        sorted_d = sorted(data)
        return {
            "count": n, "mean": round(mean, 4), "median": sorted_d[n // 2],
            "min": sorted_d[0], "max": sorted_d[-1],
            "std": round(math.sqrt(variance), 4),
            "variance": round(variance, 4),
            "sum": round(sum(data), 4),
            "range": round(sorted_d[-1] - sorted_d[0], 4),
            "q1": sorted_d[n // 4], "q3": sorted_d[3 * n // 4],
        }

    def percentile(self, name: str, p: float) -> float:
        data = sorted(self._datasets.get(name, []))
        if not data:
            return 0.0
        k = (len(data) - 1) * p / 100
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return data[int(k)]
        return data[f] * (c - k) + data[c] * (k - f)

    def correlation(self, name1: str, name2: str) -> float:
        d1 = self._datasets.get(name1, [])
        d2 = self._datasets.get(name2, [])
        n = min(len(d1), len(d2))
        if n < 2:
            return 0.0
        m1 = sum(d1[:n]) / n
        m2 = sum(d2[:n]) / n
        cov = sum((d1[i] - m1) * (d2[i] - m2) for i in range(n)) / (n - 1)
        s1 = math.sqrt(sum((x - m1) ** 2 for x in d1[:n]) / (n - 1))
        s2 = math.sqrt(sum((x - m2) ** 2 for x in d2[:n]) / (n - 1))
        if s1 == 0 or s2 == 0:
            return 0.0
        return round(cov / (s1 * s2), 4)

    def list_datasets(self) -> List[str]:
        return list(self._datasets.keys())
