"""Publishing Memory Manager — Orchestrate the full memory pipeline."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

from layers.layer07_publishing.modules.publishing_memory.publish_history import (
    PublishHistory, PublishRecord,
)
from layers.layer07_publishing.modules.publishing_memory.platform_memory import PlatformMemory
from layers.layer07_publishing.modules.publishing_memory.schedule_memory import ScheduleMemory
from layers.layer07_publishing.modules.publishing_memory.audience_memory import AudienceMemory
from layers.layer07_publishing.modules.publishing_memory.performance_memory import PerformanceMemory, PerformanceSnapshot
from layers.layer07_publishing.modules.publishing_memory.publish_failure_memory import PublishFailureMemory, FailureEntry
from layers.layer07_publishing.modules.publishing_memory.pattern_learner import PatternLearner
from layers.layer07_publishing.modules.publishing_memory.memory_search import MemorySearch, SearchFilter, SearchResult
from layers.layer07_publishing.modules.publishing_memory.memory_retention import MemoryRetention

_MANAGER_COUNTER = itertools.count(1)


class PublishingMemoryResult:
    """Result of a memory analysis query."""

    __slots__ = (
        "result_id", "best_publish_time", "best_platform",
        "best_content_type", "expected_engagement", "recommendation",
        "confidence", "patterns_found", "timestamp",
    )

    def __init__(self) -> None:
        self.result_id: str = f"pmr_{next(_MANAGER_COUNTER)}"
        self.best_publish_time: str = ""
        self.best_platform: str = ""
        self.best_content_type: str = ""
        self.expected_engagement: float = 0.0
        self.recommendation: str = ""
        self.confidence: float = 0.0
        self.patterns_found: int = 0
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "best_publish_time": self.best_publish_time,
            "best_platform": self.best_platform,
            "best_content_type": self.best_content_type,
            "expected_engagement": round(self.expected_engagement, 3),
            "recommendation": self.recommendation,
            "confidence": round(self.confidence, 3),
            "patterns_found": self.patterns_found,
        }


class PublishingMemoryManager:
    """Orchestrate the full publishing memory pipeline.

    Flow: Store → Learn → Search → Recommend → Feed Layer 9
    """

    def __init__(
        self,
        history: Optional[PublishHistory] = None,
        platform_memory: Optional[PlatformMemory] = None,
        schedule_memory: Optional[ScheduleMemory] = None,
        audience_memory: Optional[AudienceMemory] = None,
        performance_memory: Optional[PerformanceMemory] = None,
        failure_memory: Optional[PublishFailureMemory] = None,
        pattern_learner: Optional[PatternLearner] = None,
        memory_search: Optional[MemorySearch] = None,
        retention: Optional[MemoryRetention] = None,
    ) -> None:
        self.history = history or PublishHistory()
        self.platform_memory = platform_memory or PlatformMemory()
        self.schedule_memory = schedule_memory or ScheduleMemory()
        self.audience_memory = audience_memory or AudienceMemory()
        self.performance_memory = performance_memory or PerformanceMemory()
        self.failure_memory = failure_memory or PublishFailureMemory()
        self.pattern_learner = pattern_learner or PatternLearner()
        self.memory_search = memory_search or MemorySearch(self.history)
        self.retention = retention or MemoryRetention()
        self._events: List[Dict[str, Any]] = []

    def store(self, record: PublishRecord) -> PublishRecord:
        self.history.record(record)
        self.platform_memory.observe(record)
        self.schedule_memory.observe(record)
        return record

    def store_with_engagement(
        self,
        record: PublishRecord,
        engagement_rate: float = 0.0,
        content_type: str = "",
    ) -> PublishRecord:
        self.store(record)
        ct = content_type or record.content_type
        self.audience_memory.observe(ct, record.platform, engagement_rate, record.tags)
        return record

    def store_performance(self, snapshot: PerformanceSnapshot) -> None:
        self.performance_memory.record(snapshot)

    def store_failure(self, entry: FailureEntry) -> None:
        self.failure_memory.record(entry)

    def recommend(self) -> PublishingMemoryResult:
        result = PublishingMemoryResult()
        records = self.history.get_all()

        if not records:
            result.recommendation = "No history available yet. Start publishing to learn."
            result.confidence = 0.0
            return result

        # Best platform
        best_platform = self.platform_memory.get_best_platform()
        result.best_platform = best_platform or records[-1].platform

        # Best content type
        result.best_content_type = self.audience_memory.get_best_content_type()

        # Best schedule
        insight = self.schedule_memory.get_insight()
        if insight.best_hours:
            h = insight.best_hours[0]
            result.best_publish_time = f"{h:02d}:00"
        else:
            result.best_publish_time = "18:00"

        # Expected engagement
        if result.best_content_type:
            result.expected_engagement = self.audience_memory.get_avg_engagement(result.best_content_type)

        # Patterns
        patterns = self.pattern_learner.detect_patterns(records)
        result.patterns_found = len(patterns)

        # Confidence
        result.confidence = insight.confidence

        # Recommendation
        if insight.best_weekdays:
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            best_day = day_names[insight.best_weekdays[0]] if 0 <= insight.best_weekdays[0] < 7 else "any day"
            result.recommendation = (
                f"Publish on {best_day} at {result.best_publish_time} on "
                f"{result.best_platform} with {result.best_content_type} content."
            )
        else:
            result.recommendation = f"Publish on {result.best_platform} at {result.best_publish_time}."

        self._events.append({
            "event": "recommendation_generated",
            "result_id": result.result_id,
            "confidence": result.confidence,
        })
        return result

    def search(self, search_filter: SearchFilter) -> SearchResult:
        return self.memory_search.search(search_filter)

    def get_learning_signals(self) -> Dict[str, Any]:
        records = self.history.get_all()
        if not records:
            return {"available": False}
        profiles = self.platform_memory.get_all_profiles()
        return {
            "available": True,
            "total_publishes": len(records),
            "platform_count": self.platform_memory.platform_count,
            "success_rate": self.history.get_success_rate(),
            "platforms": [p.platform for p in profiles],
            "failure_rate": 1.0 - self.failure_memory.get_recovery_rate(),
        }

    def cleanup(self) -> int:
        return self.retention.cleanup(self.history)

    @property
    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)
