"""Self Reflection Engine — AI self-evaluation."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_SRE_COUNTER = itertools.count(1)


class ReflectionEntry:
    """A self-reflection entry."""

    __slots__ = ("reflection_id", "question", "answer", "insight",
                 "action_item", "timestamp")

    def __init__(self, question: str = "", answer: str = "") -> None:
        self.reflection_id: str = f"ref_{next(_SRE_COUNTER)}"
        self.question = question
        self.answer = answer
        self.insight: str = ""
        self.action_item: str = ""
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reflection_id": self.reflection_id, "question": self.question,
            "answer": self.answer, "insight": self.insight,
        }


class SelfReflectionEngine:
    """AI self-evaluation and learning reflection."""

    REFLECTION_QUESTIONS = [
        "Was the decision correct?",
        "Should we have published?",
        "Can the strategy be improved?",
        "Did we learn from this?",
        "Was a mistake repeated?",
        "What could be done differently?",
        "Is the quality improving?",
        "Are we meeting goals?",
    ]

    def __init__(self) -> None:
        self._reflections: List[ReflectionEntry] = []

    def reflect(self, question: str, answer: str, insight: str = "") -> ReflectionEntry:
        entry = ReflectionEntry(question, answer)
        entry.insight = insight
        self._reflections.append(entry)
        return entry

    def auto_reflect(self, context: Dict[str, Any]) -> List[ReflectionEntry]:
        results = []
        for q in self.REFLECTION_QUESTIONS[:3]:
            entry = ReflectionEntry(q, "pending")
            entry.insight = f"Based on context: {list(context.keys())}"
            self._reflections.append(entry)
            results.append(entry)
        return results

    def get_reflections(self, limit: int = 10) -> List[ReflectionEntry]:
        return self._reflections[-limit:]

    def get_action_items(self) -> List[str]:
        return [r.action_item for r in self._reflections if r.action_item]

    def get_stats(self) -> Dict[str, Any]:
        return {"total_reflections": len(self._reflections)}
