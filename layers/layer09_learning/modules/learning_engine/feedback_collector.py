"""Feedback Collector — Collect learning signals from all sources."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional

from layers.layer09_learning.modules.learning_engine.learning_signal import LearningSignal


class FeedbackSource:
    """Registered feedback source."""

    __slots__ = ("source_id", "name", "source_type", "fetcher", "enabled", "last_fetched")

    def __init__(self, source_id: str = "", name: str = "", source_type: str = "analytics") -> None:
        self.source_id = source_id
        self.name = name
        self.source_type = source_type
        self.fetcher: Optional[Callable] = None
        self.enabled: bool = True
        self.last_fetched: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "name": self.name,
            "source_type": self.source_type,
            "enabled": self.enabled,
        }


class FeedbackCollector:
    """Collect learning signals from multiple feedback sources."""

    def __init__(self) -> None:
        self._sources: Dict[str, FeedbackSource] = {}
        self._signals: List[LearningSignal] = []
        self._collection_count = 0

    def register_source(self, source: FeedbackSource) -> None:
        self._sources[source.source_id] = source

    def unregister_source(self, source_id: str) -> bool:
        return self._sources.pop(source_id, None) is not None

    def collect_from_source(self, source_id: str) -> List[LearningSignal]:
        source = self._sources.get(source_id)
        if not source or not source.enabled or not source.fetcher:
            return []
        try:
            raw = source.fetcher()
            signals = []
            for item in raw if isinstance(raw, list) else []:
                sig = LearningSignal(
                    source=source.source_type,
                    signal_type=item.get("type", "engagement"),
                    metric_name=item.get("metric", ""),
                    value=item.get("value", 0.0),
                )
                sig.platform = item.get("platform", "")
                sig.content_id = item.get("content_id", "")
                signals.append(sig)
            self._signals.extend(signals)
            source.last_fetched = time.time()
            self._collection_count += 1
            return signals
        except Exception:
            return []

    def collect_all(self) -> List[LearningSignal]:
        all_signals: List[LearningSignal] = []
        for source_id in self._sources:
            all_signals.extend(self.collect_from_source(source_id))
        return all_signals

    def add_signal(self, signal: LearningSignal) -> None:
        self._signals.append(signal)

    def get_signals(
        self,
        source: str = "",
        signal_type: str = "",
        platform: str = "",
        limit: int = 100,
    ) -> List[LearningSignal]:
        result = self._signals
        if source:
            result = [s for s in result if s.source == source]
        if signal_type:
            result = [s for s in result if s.signal_type == signal_type]
        if platform:
            result = [s for s in result if s.platform == platform]
        return result[-limit:]

    def get_sources(self) -> List[FeedbackSource]:
        return list(self._sources.values())

    @property
    def signal_count(self) -> int:
        return len(self._signals)

    @property
    def collection_count(self) -> int:
        return self._collection_count
