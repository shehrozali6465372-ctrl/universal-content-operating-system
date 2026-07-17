"""Benchmark Manager — Manage quality benchmarks and comparisons."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List, Optional

_BM_COUNTER = itertools.count(1)


class BenchmarkRun:
    """A single benchmark run with results."""

    __slots__ = ("run_id", "benchmark_name", "scores", "metrics",
                 "created_at", "duration_ms", "tags")

    def __init__(self, benchmark_name: str = "") -> None:
        self.run_id: str = f"bch_{next(_BM_COUNTER)}"
        self.benchmark_name = benchmark_name
        self.scores: Dict[str, float] = {}
        self.metrics: Dict[str, Any] = {}
        self.created_at: float = time.time()
        self.duration_ms: float = 0.0
        self.tags: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "benchmark_name": self.benchmark_name,
            "scores": {k: round(v, 4) for k, v in self.scores.items()},
            "created_at": self.created_at,
            "duration_ms": round(self.duration_ms, 1),
        }


class BenchmarkManager:
    """Manage benchmark runs and measure improvements over time."""

    def __init__(self) -> None:
        self._runs: List[BenchmarkRun] = []

    def create_run(self, name: str, scores: Dict[str, float],
                   duration_ms: float = 0.0,
                   tags: Optional[List[str]] = None) -> BenchmarkRun:
        run = BenchmarkRun(name)
        run.scores = dict(scores)
        run.duration_ms = duration_ms
        if tags:
            run.tags = list(tags)
        self._runs.append(run)
        return run

    def get_latest(self, name: str) -> Optional[BenchmarkRun]:
        matching = [r for r in self._runs if r.benchmark_name == name]
        return matching[-1] if matching else None

    def compare_runs(self, name: str, count: int = 2) -> List[BenchmarkRun]:
        matching = [r for r in self._runs if r.benchmark_name == name]
        return matching[-count:]

    def get_improvement(self, name: str) -> float:
        runs = self.compare_runs(name, 2)
        if len(runs) < 2:
            return 0.0
        first_avg = sum(runs[0].scores.values()) / max(1, len(runs[0].scores))
        last_avg = sum(runs[-1].scores.values()) / max(1, len(runs[-1].scores))
        if first_avg == 0:
            return 0.0
        return round(((last_avg - first_avg) / abs(first_avg)) * 100, 2)

    def get_best_run(self, name: str) -> Optional[BenchmarkRun]:
        matching = [r for r in self._runs if r.benchmark_name == name]
        if not matching:
            return None
        return max(matching, key=lambda r: sum(r.scores.values()) / max(1, len(r.scores)))

    def get_all_names(self) -> List[str]:
        return list(set(r.benchmark_name for r in self._runs))

    def get_recent(self, count: int = 10) -> List[BenchmarkRun]:
        return list(self._runs[-count:])

    @property
    def run_count(self) -> int:
        return len(self._runs)
