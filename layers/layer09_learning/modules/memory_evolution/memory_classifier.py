"""Memory Classifier — Classify memory entries by type, importance, and age."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


MEMORY_CATEGORIES = ("lesson", "mistake", "insight", "pattern", "optimization", "strategy")
MEMORY_IMPORTANCE = ("critical", "high", "medium", "low")
MEMORY_LIFECYCLE = ("active", "mature", "aging", "expired", "archived")


class ClassifiedMemory:
    """A memory entry with classification metadata."""

    __slots__ = ("memory_id", "source_type", "category", "importance",
                 "lifecycle", "confidence", "usage_count", "age_days",
                 "tags", "score")

    def __init__(self, memory_id: str = "", source_type: str = "lesson") -> None:
        self.memory_id = memory_id
        self.source_type = source_type
        self.category: str = "insight"
        self.importance: str = "medium"
        self.lifecycle: str = "active"
        self.confidence: float = 0.5
        self.usage_count: int = 0
        self.age_days: float = 0.0
        self.tags: List[str] = []
        self.score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "category": self.category,
            "importance": self.importance,
            "lifecycle": self.lifecycle,
            "confidence": round(self.confidence, 3),
            "score": round(self.score, 3),
        }


class MemoryClassifier:
    """Classify memory entries by importance, lifecycle, and category."""

    def __init__(self) -> None:
        self._classified: List[ClassifiedMemory] = []
        self._classification_count: int = 0

    def classify(self, memory_id: str, source_type: str = "lesson",
                 confidence: float = 0.5, usage_count: int = 0,
                 age_days: float = 0.0, tags: Optional[List[str]] = None) -> ClassifiedMemory:
        cm = ClassifiedMemory(memory_id, source_type)
        cm.confidence = confidence
        cm.usage_count = usage_count
        cm.age_days = age_days
        cm.tags = tags or []
        cm.category = self._determine_category(source_type)
        cm.importance = self._determine_importance(confidence, usage_count)
        cm.lifecycle = self._determine_lifecycle(age_days, usage_count)
        cm.score = self._compute_score(cm)
        self._classified.append(cm)
        self._classification_count += 1
        return cm

    def classify_batch(self, entries: List[Dict[str, Any]]) -> List[ClassifiedMemory]:
        results = []
        for e in entries:
            cm = self.classify(
                memory_id=e.get("memory_id", ""),
                source_type=e.get("source_type", "lesson"),
                confidence=e.get("confidence", 0.5),
                usage_count=e.get("usage_count", 0),
                age_days=e.get("age_days", 0.0),
                tags=e.get("tags", []),
            )
            results.append(cm)
        return results

    def _determine_category(self, source_type: str) -> str:
        mapping = {
            "lesson": "lesson", "mistake": "mistake", "insight": "insight",
            "pattern": "pattern", "optimization": "optimization", "strategy": "strategy",
        }
        return mapping.get(source_type, "insight")

    def _determine_importance(self, confidence: float, usage_count: int) -> str:
        score = confidence * 0.6 + min(1.0, usage_count / 10.0) * 0.4
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.3:
            return "medium"
        return "low"

    def _determine_lifecycle(self, age_days: float, usage_count: int) -> str:
        if age_days > 90 and usage_count < 2:
            return "expired"
        elif age_days > 60:
            return "aging"
        elif age_days > 30:
            return "mature"
        return "active"

    def _compute_score(self, cm: ClassifiedMemory) -> float:
        importance_weights = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2}
        lifecycle_weights = {"active": 1.0, "mature": 0.8, "aging": 0.5, "expired": 0.1, "archived": 0.0}
        imp = importance_weights.get(cm.importance, 0.5)
        life = lifecycle_weights.get(cm.lifecycle, 0.5)
        usage = min(1.0, cm.usage_count / 10.0)
        return round(imp * 0.4 + life * 0.3 + cm.confidence * 0.2 + usage * 0.1, 3)

    def get_by_importance(self, importance: str) -> List[ClassifiedMemory]:
        return [c for c in self._classified if c.importance == importance]

    def get_by_lifecycle(self, lifecycle: str) -> List[ClassifiedMemory]:
        return [c for c in self._classified if c.lifecycle == lifecycle]

    def get_classified(self) -> List[ClassifiedMemory]:
        return list(self._classified)

    @property
    def classification_count(self) -> int:
        return self._classification_count
