"""Production-safe analytics data collection with provenance and persistence hooks."""
from __future__ import annotations

import math
import time
from threading import RLock
from typing import Any, Callable, Dict, List, Optional

from layers.layer08_analytics.modules.exceptions import DataCollectionError


class DataPoint:
    """Immutable-by-convention analytics observation."""

    __slots__ = ("source", "metric_name", "value", "timestamp", "dimensions", "metadata")

    def __init__(self, source: str = "", metric_name: str = "", value: float = 0.0) -> None:
        if not source.strip() or not metric_name.strip():
            raise ValueError("source and metric_name are required")
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError("value must be a finite number")
        self.source = source.strip()
        self.metric_name = metric_name.strip()
        self.value = float(value)
        self.timestamp = time.time()
        self.dimensions: Dict[str, str] = {}
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source, "metric_name": self.metric_name,
            "value": self.value, "timestamp": self.timestamp,
            "dimensions": dict(self.dimensions), "metadata": dict(self.metadata),
        }


class DataSource:
    """Registered source. Fetchers must return a mapping of metric names to values."""

    __slots__ = ("source_id", "name", "fetcher", "interval_seconds",
                 "last_fetched", "enabled", "tags")

    def __init__(self, source_id: str = "", name: str = "",
                 fetcher: Optional[Callable[[], Dict[str, Any]]] = None) -> None:
        if not source_id.strip():
            raise ValueError("source_id is required")
        self.source_id = source_id.strip()
        self.name = name.strip()
        self.fetcher = fetcher
        self.interval_seconds = 3600
        self.last_fetched = 0.0
        self.enabled = True
        self.tags: List[str] = []

    def is_ready(self) -> bool:
        return time.time() - self.last_fetched >= max(0, self.interval_seconds)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id, "name": self.name, "enabled": self.enabled,
            "last_fetched": self.last_fetched, "tags": list(self.tags),
        }


class DataCollector:
    """Collect, validate, retain, and optionally durably persist observations."""

    def __init__(self, persist: Optional[Callable[[DataPoint], None]] = None) -> None:
        self._sources: Dict[str, DataSource] = {}
        self._data_points: List[DataPoint] = []
        self._collection_count = 0
        self._last_collection = 0.0
        self._persist = persist
        self._lock = RLock()

    def register_source(self, source: DataSource) -> None:
        with self._lock:
            if source.source_id in self._sources:
                raise ValueError(f"source already registered: {source.source_id}")
            self._sources[source.source_id] = source

    def unregister_source(self, source_id: str) -> bool:
        with self._lock:
            return self._sources.pop(source_id, None) is not None

    def collect(self, source_id: str) -> List[DataPoint]:
        with self._lock:
            source = self._sources.get(source_id)
            if not source or not source.enabled or not source.fetcher:
                return []
            if not source.is_ready():
                return []
            fetcher = source.fetcher
        try:
            raw_data = fetcher()
            if not isinstance(raw_data, dict):
                raise DataCollectionError("data source must return a mapping")
            points: List[DataPoint] = []
            for name, value in raw_data.items():
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    continue
                point = DataPoint(source_id, str(name), float(value))
                points.append(point)
            for point in points:
                if self._persist is not None:
                    try:
                        self._persist(point)
                    except Exception as exc:
                        raise DataCollectionError(
                            f"durable persistence failed for {source_id}:{point.metric_name}"
                        ) from exc
            with self._lock:
                self._data_points.extend(points)
                source.last_fetched = time.time()
                self._collection_count += 1
            return points
        except DataCollectionError:
            raise
        except Exception as exc:
            raise DataCollectionError(f"collection failed for source {source_id}") from exc

    def collect_all(self) -> List[DataPoint]:
        all_points: List[DataPoint] = []
        errors: List[str] = []
        for source_id in list(self._sources):
            try:
                all_points.extend(self.collect(source_id))
            except DataCollectionError as exc:
                errors.append(str(exc))
        self._last_collection = time.time()
        if errors:
            raise DataCollectionError("; ".join(errors))
        return all_points

    def collect_manual(self, source: str, metric_name: str, value: float, **dims: str) -> DataPoint:
        point = DataPoint(source, metric_name, value)
        point.dimensions.update({str(k): str(v) for k, v in dims.items()})
        if self._persist is not None:
            try:
                self._persist(point)
            except Exception as exc:
                raise DataCollectionError("durable persistence failed") from exc
        with self._lock:
            self._data_points.append(point)
        return point

    def get_data(self, source: str = "", metric: str = "", limit: int = 100) -> List[DataPoint]:
        if limit < 0:
            raise ValueError("limit must be non-negative")
        with self._lock:
            result = list(self._data_points)
        if source:
            result = [p for p in result if p.source == source]
        if metric:
            result = [p for p in result if p.metric_name == metric]
        return result[-limit:] if limit else []

    def get_sources(self) -> List[DataSource]:
        with self._lock:
            return list(self._sources.values())

    def get_source(self, source_id: str) -> Optional[DataSource]:
        with self._lock:
            return self._sources.get(source_id)

    def get_ready_sources(self) -> List[DataSource]:
        return [s for s in self.get_sources() if s.enabled and s.is_ready()]

    @property
    def total_points(self) -> int:
        with self._lock:
            return len(self._data_points)

    @property
    def collection_count(self) -> int:
        with self._lock:
            return self._collection_count
