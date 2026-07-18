"""learning_memory_store.py — Learning memory persistence."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer13_persistence.modules.ai_memory_persistence.base_memory_store import BaseMemoryStore, MemoryEntry


class Lesson:
    """A learned lesson."""
    __slots__ = ("lesson_id", "category", "description", "impact",
                 "confidence", "source_events", "created_at")
    _counter = 0

    def __init__(self, category: str, description: str, impact: str = "medium") -> None:
        Lesson._counter += 1
        self.lesson_id: int = Lesson._counter
        self.category = category
        self.description = description
        self.impact = impact
        self.confidence: float = 0.5
        self.source_events: List[str] = []
        import time
        self.created_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.lesson_id, "category": self.category,
                "description": self.description, "impact": self.impact}


class LearningMemoryStore(BaseMemoryStore):
    """Stores learned lessons and improvements."""

    def __init__(self, max_entries: int = 5000) -> None:
        super().__init__("learning", max_entries)
        self._lessons: Dict[str, Lesson] = {}
        self._mistakes: List[Dict[str, Any]] = []

    def store(self, key: str, value: Any, metadata: Dict[str, Any] = None) -> MemoryEntry:
        entry = MemoryEntry(key, value, "learning")
        if metadata:
            entry.metadata = metadata
        self._store[key] = entry
        return entry

    def retrieve(self, key: str) -> Optional[MemoryEntry]:
        entry = self._store.get(key)
        if entry:
            entry.access_count += 1
        return entry

    def add_lesson(self, lesson: Lesson) -> None:
        self._lessons[lesson.category + "_" + str(lesson.lesson_id)] = lesson

    def get_lessons(self, category: str = "") -> List[Lesson]:
        lessons = list(self._lessons.values())
        if category:
            lessons = [l for l in lessons if l.category == category]
        return lessons

    def record_mistake(self, mistake: Dict[str, Any]) -> None:
        import time
        mistake["timestamp"] = time.time()
        self._mistakes.append(mistake)

    def get_mistakes(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._mistakes[-limit:]

    def stats(self) -> Dict[str, Any]:
        base = super().stats()
        base["lessons"] = len(self._lessons)
        base["mistakes"] = len(self._mistakes)
        return base
