"""Data Collector — Collect analytics data from all sources."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional


class DataPoint:
    """Single data point collected from a source."""

    __slots__ = ("source", "metric_name", "value", "timestamp",
                 "dimensions", "metadata")

    def __init__(self, source: str = "", metric_name: str = "", value: float = 0.0) -> None:
        self.source = source
        self.metric_name = metric_name
        self.value = value
        self.timestamp: float = time.time()
        self.dimensions: Dict[str, str] = {}
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "metric_name": self.metric_name,
            "value": self.value,
            "timestamp": self.timestamp,
            "dimensions": self.dimensions,
        }


class DataSource:
    """Registered data source configuration."""

    __slots__ = ("source_id", "name", "fetcher", "interval_seconds",
                 "last_fetched", "enabled", "tags")

    def __init__(self, source_id: str = "", name: str = "", fetcher: Optional[Callable] = None) -> None:
        self.source_id = source_id
        self.name = name
        self.fetcher = fetcher
        self.interval_seconds: int = 3600
        self.last_fetched: float = 0.0
        self.enabled: bool = True
        self.tags: List[str] = []

    def is_ready(self) -> bool:
        return time.time() - self.last_fetched >= self.interval_seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "name": self.name,
            "enabled": self.enabled,
            "last_fetched": self.last_fetched,
            "tags": self.tags,
        }


class DataCollector:
    """Collect analytics data from multiple sources."""

    def __init__(self) -> None:
        self._sources: Dict[str, DataSource] = {}
        self._data_points: List[DataPoint] = []
        self._collection_count = 0
        self._last_collection: float = 0.0

    def register_source(self, source: DataSource) -> None:
        self._sources[source.source_id] = source

    def unregister_source(self, source_id: str) -> bool:
        if source_id in self._sources:
            del self._sources[source_id]
            return True
        return False

    def collect(self, source_id: str) -> List[DataPoint]:
        source = self._sources.get(source_id)
        if not source or not source.enabled:
            return []
        if not source.fetcher:
            return []
        try:
            raw_data = source.fetcher()
            points = []
            for name, value in raw_data.items():
                if isinstance(value, (int, float)):
                    dp = DataPoint(source=source_id, metric_name=name, value=float(value))
                    points.append(dp)
            self._data_points.extend(points)
            source.last_fetched = time.time()
            self._collection_count += 1
            return points
        except Exception:
            return []

    def collect_all(self) -> List[DataPoint]:
        all_points: List[DataPoint] = []
        for source_id in self._sources:
            all_points.extend(self.collect(source_id))
        self._last_collection = time.time()
        return all_points

    def collect_manual(self, source: str, metric_name: str, value: float, **dims: str) -> DataPoint:
        dp = DataPoint(source=source, metric_name=metric_name, value=value)
        dp.dimensions.update(dims)
        self._data_points.append(dp)
        return dp

    def get_data(self, source: str = "", metric: str = "", limit: int = 100) -> List[DataPoint]:
        result = self._data_points
        if source:
            result = [p for p in result if p.source == source]
        if metric:
            result = [p for p in result if p.metric_name == metric]
        return result[-limit:]

    def get_sources(self) -> List[DataSource]:
        return list(self._sources.values())

    def get_source(self, source_id: str) -> Optional[DataSource]:
        return self._sources.get(source_id)

    def get_ready_sources(self) -> List[DataSource]:
        return [s for s in self._sources.values() if s.enabled and s.is_ready()]

    @property
    def total_points(self) -> int:
        return len(self._data_points)

    @property
    def collection_count(self) -> int:
        return self._collection_count
