"""query_analyzer.py — Query analysis and profiling."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class QueryProfile:
    """Profile of a query execution."""
    __slots__ = ("sql", "execution_time_ms", "rows_scanned", "rows_returned",
                 "index_used", "timestamp")

    def __init__(self, sql: str, execution_ms: float = 0.0) -> None:
        self.sql = sql
        self.execution_time_ms = execution_ms
        self.rows_scanned: int = 0
        self.rows_returned: int = 0
        self.index_used: bool = False
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"sql": self.sql[:200], "execution_ms": self.execution_time_ms,
                "rows_scanned": self.rows_scanned, "index_used": self.index_used}


class QueryAnalyzer:
    """Analyzes query performance."""

    def __init__(self) -> None:
        self._profiles: List[QueryProfile] = []

    def profile(self, sql: str, execution_ms: float = 0.0) -> QueryProfile:
        p = QueryProfile(sql, execution_ms)
        self._profiles.append(p)
        return p

    def get_slow_queries(self, threshold_ms: float = 100.0) -> List[QueryProfile]:
        return [p for p in self._profiles if p.execution_time_ms > threshold_ms]

    def get_all_profiles(self) -> List[QueryProfile]:
        return list(self._profiles)

    def get_avg_time(self) -> float:
        if not self._profiles:
            return 0.0
        return sum(p.execution_time_ms for p in self._profiles) / len(self._profiles)

    def stats(self) -> Dict[str, Any]:
        return {"total_profiles": len(self._profiles),
                "avg_time_ms": self.get_avg_time(),
                "slow_queries": len(self.get_slow_queries())}
