"""Novelty Engine - Boosts novel/rare recommendations."""
from __future__ import annotations
from typing import Any, Dict, List


class NoveltyResult:
    __slots__ = ("scored", "novelty_bonus", "novel_count")
    def __init__(self) -> None:
        self.scored: List[Dict] = []
        self.novelty_bonus = 0.0
        self.novel_count = 0
    def to_dict(self) -> Dict:
        return {"novel_count": self.novel_count, "novelty_bonus": round(self.novelty_bonus, 3)}


class NoveltyEngine:
    def __init__(self, history_topics: List[str] = None, bonus_weight: float = 0.1) -> None:
        self._history = set(t.lower() for t in (history_topics or []))
        self._bonus = bonus_weight

    def score_novelty(self, candidates: List[Any]) -> NoveltyResult:
        result = NoveltyResult()
        for c in candidates:
            is_novel = c.topic.lower() not in self._history
            bonus = self._bonus if is_novel else 0.0
            if is_novel:
                result.novel_count += 1
            result.scored.append({"topic": c.topic, "novel": is_novel, "bonus": bonus})
        result.novelty_bonus = result.novel_count / max(len(candidates), 1) * self._bonus
        return result

    def add_to_history(self, topic: str) -> None:
        self._history.add(topic.lower())
