"""Layer 8 persistence boundary; Layer 13 owns the PostgreSQL connection lifecycle."""
from __future__ import annotations
from typing import Any, Dict, Protocol


class AnalyticsPersistence(Protocol):
    durable: bool
    def record_metric(self, metric_name: str, value: float, dimensions: Dict[str, Any]) -> int:
        ...


class PostgreSQLAnalyticsPersistence:
    """Adapter over the real Layer 13 PostgreSQL AnalyticsRepository.

    The adapter is fail-closed: an in-memory repository is never labelled durable.
    It does not create, own, or close the Layer 13 connection pool.
    """
    def __init__(self, analytics_repository: Any) -> None:
        record = getattr(analytics_repository, "record", None)
        pool = getattr(analytics_repository, "_pool", None)
        insert = getattr(pool, "insert", None)
        if analytics_repository is None or not callable(record) or not callable(insert):
            raise ValueError("a PostgreSQL-backed Layer 13 AnalyticsRepository is required")
        self._repository = analytics_repository
        self.durable = True

    def record_metric(self, metric_name: str, value: float, dimensions: Dict[str, Any]) -> int:
        return int(self._repository.record(metric_name, float(value), dict(dimensions or {})))
