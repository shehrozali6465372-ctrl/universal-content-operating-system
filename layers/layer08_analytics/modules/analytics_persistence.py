"""Layer 8 persistence boundary; Layer 13 owns the actual database connection."""
from __future__ import annotations
from typing import Any, Dict, Protocol


class AnalyticsPersistence(Protocol):
    """Durable sink implemented by the Layer 13 persistence boundary."""
    durable: bool
    def record_metric(self, metric_name: str, value: float, dimensions: Dict[str, Any]) -> int:
        ...


class PostgreSQLAnalyticsPersistence:
    """Adapter over Layer 13's AnalyticsRepository; never creates its own pool."""
    durable = True
    def __init__(self, analytics_repository: Any) -> None:
        if analytics_repository is None or not callable(getattr(analytics_repository, "record", None)):
            raise ValueError("a Layer 13 AnalyticsRepository is required")
        self._repository = analytics_repository
    def record_metric(self, metric_name: str, value: float, dimensions: Dict[str, Any]) -> int:
        return int(self._repository.record(metric_name, float(value), dimensions))
