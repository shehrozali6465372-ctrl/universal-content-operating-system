"""Lesson Generator — Convert patterns into actionable lessons."""
from __future__ import annotations
import itertools
from typing import Any, Dict, List

from layers.layer09_learning.modules.learning_engine.pattern_detector import DetectedPattern

_LESSON_COUNTER = itertools.count(1)

LESSON_TYPES = ("best_practice", "mistake", "insight", "warning", "recommendation")


class Lesson:
    """A generated lesson from detected patterns."""

    __slots__ = ("lesson_id", "lesson_type", "title", "description",
                 "source_pattern", "confidence", "action_items",
                 "platform", "category", "version")

    def __init__(self, lesson_type: str = "insight", title: str = "") -> None:
        self.lesson_id: str = f"lesn_{next(_LESSON_COUNTER)}"
        self.lesson_type = lesson_type if lesson_type in LESSON_TYPES else "insight"
        self.title = title
        self.description: str = ""
        self.source_pattern: str = ""
        self.confidence: float = 0.0
        self.action_items: List[str] = []
        self.platform: str = ""
        self.category: str = ""
        self.version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lesson_id": self.lesson_id,
            "lesson_type": self.lesson_type,
            "title": self.title,
            "description": self.description,
            "confidence": round(self.confidence, 3),
            "action_items": self.action_items,
            "platform": self.platform,
            "version": self.version,
        }


class LessonGenerator:
    """Generate lessons from detected patterns."""

    def __init__(self) -> None:
        self._lessons: List[Lesson] = []
        self._generation_count = 0

    def generate(self, patterns: List[DetectedPattern]) -> List[Lesson]:
        new_lessons: List[Lesson] = []
        for pattern in patterns:
            if pattern.pattern_type == "success":
                lesson = self._from_success_pattern(pattern)
            elif pattern.pattern_type == "failure":
                lesson = self._from_failure_pattern(pattern)
            elif pattern.pattern_type == "repeated":
                lesson = self._from_repeated_pattern(pattern)
            else:
                lesson = self._from_generic_pattern(pattern)
            if lesson:
                new_lessons.append(lesson)
                self._lessons.append(lesson)
        self._generation_count += 1
        return new_lessons

    def _from_success_pattern(self, pattern: DetectedPattern) -> Lesson:
        lesson = Lesson("best_practice", f"Success pattern on {pattern.platform or 'multiple platforms'}")
        lesson.description = pattern.description
        lesson.source_pattern = pattern.pattern_id
        lesson.confidence = pattern.confidence
        lesson.platform = pattern.platform
        lesson.action_items = [
            f"Replicate this approach (observed {pattern.frequency} times)",
            "Document the exact content strategy used",
        ]
        return lesson

    def _from_failure_pattern(self, pattern: DetectedPattern) -> Lesson:
        lesson = Lesson("mistake", f"Recurring failure: {pattern.tags[0] if pattern.tags else 'unknown'}")
        lesson.description = pattern.description
        lesson.source_pattern = pattern.pattern_id
        lesson.confidence = pattern.confidence
        lesson.action_items = [
            f"Investigate root cause of {pattern.tags[0] if pattern.tags else 'failure'}",
            "Consider alternative approach",
        ]
        return lesson

    def _from_repeated_pattern(self, pattern: DetectedPattern) -> Lesson:
        lesson = Lesson("insight", f"Consistent behaviour: {pattern.description[:50]}")
        lesson.description = pattern.description
        lesson.source_pattern = pattern.pattern_id
        lesson.confidence = pattern.confidence
        lesson.action_items = ["This is a stable pattern — maintain current approach"]
        return lesson

    def _from_generic_pattern(self, pattern: DetectedPattern) -> Lesson:
        lesson = Lesson("recommendation", f"Pattern detected: {pattern.description[:50]}")
        lesson.description = pattern.description
        lesson.source_pattern = pattern.pattern_id
        lesson.confidence = pattern.confidence
        lesson.action_items = ["Review and decide on action"]
        return lesson

    def get_lessons(self, lesson_type: str = "", platform: str = "") -> List[Lesson]:
        result = self._lessons
        if lesson_type:
            result = [l for l in result if l.lesson_type == lesson_type]
        if platform:
            result = [l for l in result if l.platform == platform]
        return result

    def get_all_lessons(self) -> List[Lesson]:
        return list(self._lessons)

    @property
    def lesson_count(self) -> int:
        return len(self._lessons)

    @property
    def generation_count(self) -> int:
        return self._generation_count
