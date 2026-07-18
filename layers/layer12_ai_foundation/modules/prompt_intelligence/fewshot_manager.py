"""FewShotManager — manage and select few-shot examples for in-context learning."""
from __future__ import annotations

from typing import Any, Dict, List

from .models import FewShotExample


class FewShotManager:
    """Manage and select few-shot examples for in-context learning."""

    def __init__(self, max_examples: int = 10) -> None:
        self.max_examples = max_examples
        self._examples: List[FewShotExample] = []

    def add(self, example: FewShotExample) -> None:
        self._examples.append(example)

    def remove(self, example_id: str) -> bool:
        before = len(self._examples)
        self._examples = [e for e in self._examples if e.example_id != example_id]
        return len(self._examples) < before

    def get_for_prompt(self, task: str = "", limit: int = 3,
                       category: str = "") -> List[FewShotExample]:
        candidates = self._examples
        if category:
            candidates = [e for e in candidates if e.category == category]
        if task:
            for e in candidates:
                e.relevance_score = self._calculate_relevance(e, task)
            candidates = sorted(candidates, key=lambda e: e.relevance_score, reverse=True)
        return candidates[:limit]

    def get_by_category(self, category: str) -> List[FewShotExample]:
        return [e for e in self._examples if e.category == category]

    def count(self) -> int:
        return len(self._examples)

    def clear(self) -> None:
        self._examples.clear()

    @staticmethod
    def _calculate_relevance(example: FewShotExample, task: str) -> float:
        task_words = set(task.lower().split())
        example_words = set((example.input_text + " " + example.output_text).lower().split())
        if not task_words:
            return 0.0
        overlap = task_words & example_words
        return len(overlap) / len(task_words)

    def to_dict(self) -> Dict[str, Any]:
        return {"count": len(self._examples),
                "categories": list(set(e.category for e in self._examples if e.category))}
