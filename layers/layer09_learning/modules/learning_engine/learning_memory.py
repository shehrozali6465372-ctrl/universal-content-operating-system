"""Learning Memory — Store and retrieve lessons with version history."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List, Optional

from layers.layer09_learning.modules.learning_engine.lesson_generator import Lesson
from layers.layer09_learning.modules.learning_engine.improvement_planner import Improvement

_MEMORY_COUNTER = itertools.count(1)


class MemoryEntry:
    """A stored learning memory entry."""

    __slots__ = ("entry_id", "lesson", "improvement", "version",
                 "created_at", "tags", "archived")

    def __init__(self, lesson: Optional[Lesson] = None, improvement: Optional[Improvement] = None) -> None:
        self.entry_id: str = f"mem_{next(_MEMORY_COUNTER)}"
        self.lesson = lesson
        self.improvement = improvement
        self.version: int = 1
        self.created_at: float = time.time()
        self.tags: List[str] = []
        self.archived: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "version": self.version,
            "has_lesson": self.lesson is not None,
            "has_improvement": self.improvement is not None,
            "tags": self.tags,
            "archived": self.archived,
            "created_at": self.created_at,
        }


class LearningMemory:
    """Store and retrieve learning outcomes."""

    def __init__(self, max_entries: int = 10000) -> None:
        self._max_entries = max_entries
        self._entries: List[MemoryEntry] = []
        self._index: Dict[str, List[int]] = {}

    def store_lesson(self, lesson: Lesson) -> MemoryEntry:
        entry = MemoryEntry(lesson=lesson)
        entry.tags.append(lesson.lesson_type)
        if lesson.platform:
            entry.tags.append(lesson.platform)
        self._add_entry(entry)
        return entry

    def store_improvement(self, improvement: Improvement) -> MemoryEntry:
        entry = MemoryEntry(improvement=improvement)
        entry.tags.append(improvement.priority)
        if improvement.platform:
            entry.tags.append(improvement.platform)
        self._add_entry(entry)
        return entry

    def store_batch(self, lessons: List[Lesson], improvements: List[Improvement]) -> int:
        count = 0
        for lesson in lessons:
            self.store_lesson(lesson)
            count += 1
        for imp in improvements:
            self.store_improvement(imp)
            count += 1
        return count

    def search(self, tag: str = "", lesson_type: str = "", platform: str = "",
               limit: int = 50) -> List[MemoryEntry]:
        results = [e for e in self._entries if not e.archived]
        if tag:
            results = [e for e in results if tag in e.tags]
        if lesson_type:
            results = [e for e in results if e.lesson and e.lesson.lesson_type == lesson_type]
        if platform:
            results = [e for e in results if platform in e.tags]
        return results[-limit:]

    def get_recent(self, count: int = 10) -> List[MemoryEntry]:
        return [e for e in self._entries if not e.archived][-count:]

    def get_by_id(self, entry_id: str) -> Optional[MemoryEntry]:
        for e in self._entries:
            if e.entry_id == entry_id:
                return e
        return None

    def archive(self, entry_id: str) -> bool:
        entry = self.get_by_id(entry_id)
        if entry:
            entry.archived = True
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        active = [e for e in self._entries if not e.archived]
        lessons = sum(1 for e in active if e.lesson)
        improvements = sum(1 for e in active if e.improvement)
        return {
            "total": len(self._entries),
            "active": len(active),
            "archived": len(self._entries) - len(active),
            "lessons": lessons,
            "improvements": improvements,
        }

    def _add_entry(self, entry: MemoryEntry) -> None:
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]

    @property
    def entry_count(self) -> int:
        return len([e for e in self._entries if not e.archived])
