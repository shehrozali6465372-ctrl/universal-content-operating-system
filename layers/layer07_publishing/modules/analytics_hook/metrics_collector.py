"""Metrics Collector — Fetch analytics from platform plugins."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional

from layers.layer07_publishing.modules.analytics_hook.analytics_event import AnalyticsEvent
from layers.layer07_publishing.modules.analytics_hook.exceptions import FetchError


class MetricsCollector:
    """Collect analytics data from platform plugins."""

    def __init__(self) -> None:
        self._collection_count = 0
        self._total_fetch_time_ms = 0.0

    def collect_single(
        self,
        platform: str,
        post_id: str,
        fetcher: Callable[[str, str], Dict[str, Any]],
    ) -> Optional[AnalyticsEvent]:
        start = time.time()
        try:
            raw = fetcher(platform, post_id)
        except Exception as e:
            raise FetchError(f"Failed to fetch from {platform}: {e}") from e
        elapsed = (time.time() - start) * 1000
        self._collection_count += 1
        self._total_fetch_time_ms += elapsed

        event = AnalyticsEvent(platform=platform, post_id=post_id)
        event.metrics = self._flatten_metrics(raw)
        event.collected_at = time.time()
        return event

    def collect_batch(
        self,
        posts: List[Dict[str, str]],
        fetcher: Callable[[str, str], Dict[str, Any]],
    ) -> List[AnalyticsEvent]:
        events: List[AnalyticsEvent] = []
        for item in posts:
            platform = item.get("platform", "")
            post_id = item.get("post_id", "")
            if platform and post_id:
                try:
                    event = self.collect_single(platform, post_id, fetcher)
                    if event:
                        events.append(event)
                except FetchError:
                    pass
        return events

    def _flatten_metrics(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        flat: Dict[str, Any] = {}
        for key, val in raw.items():
            if isinstance(val, (int, float)):
                flat[key] = val
            elif isinstance(val, dict):
                for k2, v2 in val.items():
                    if isinstance(v2, (int, float)):
                        flat[k2] = v2
            elif isinstance(val, str):
                flat[key] = val
        return flat

    @property
    def collection_count(self) -> int:
        return self._collection_count

    @property
    def avg_fetch_time_ms(self) -> float:
        return self._total_fetch_time_ms / max(1, self._collection_count)
