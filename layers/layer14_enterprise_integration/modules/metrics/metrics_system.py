"""MetricsSystem — collect, aggregate, and expose metrics across all layers."""
from __future__ import annotations
import time
from typing import Any, Dict, List

class MetricsSystem:
    def __init__(self) -> None:
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._start = time.time()

    def increment(self, name: str, value: int = 1) -> None:
        self._counters[name] = self._counters.get(name, 0) + value
    def gauge(self, name: str, value: float) -> None:
        self._gauges[name] = value
    def histogram(self, name: str, value: float) -> None:
        self._histograms.setdefault(name, []).append(value)
    def get_counter(self, name: str) -> int:
        return self._counters.get(name, 0)
    def get_gauge(self, name: str) -> float:
        return self._gauges.get(name, 0.0)
    def histogram_stats(self, name: str) -> Dict[str, float]:
        values = self._histograms.get(name, [])
        if not values: return {'count': 0, 'avg': 0.0, 'min': 0.0, 'max': 0.0, 'p95': 0.0}
        sorted_v = sorted(values)
        p95_idx = int(len(sorted_v) * 0.95)
        return {'count': len(values), 'avg': round(sum(values) / len(values), 2),
                'min': sorted_v[0], 'max': sorted_v[-1],
                'p95': sorted_v[min(p95_idx, len(sorted_v) - 1)]}

    def export_all(self) -> Dict[str, Any]:
        return {'uptime': round(time.time() - self._start, 2),
                'counters': dict(self._counters), 'gauges': dict(self._gauges),
                'histograms': {k: self.histogram_stats(k) for k in self._histograms}}

    def prometheus_format(self) -> str:
        lines: List[str] = []
        for k, v in self._counters.items():
            lines.append(f'aios_counter_{k} {v}')
        for k, v in self._gauges.items():
            lines.append(f'aios_gauge_{k} {v}')
        stats = {k: self.histogram_stats(k) for k in self._histograms}
        for k, s in stats.items():
            lines.append(f'aios_histogram_{k}_avg {s["avg"]}')
            lines.append(f'aios_histogram_{k}_p95 {s["p95"]}')
        return '\n'.join(lines)

    def reset(self) -> None:
        self._counters.clear(); self._gauges.clear(); self._histograms.clear()
