"""Novelty Detector - Detects content uniqueness vs existing content."""
from __future__ import annotations
import hashlib
from typing import Dict, List, Optional


class NoveltyResult:
    __slots__ = ("novelty_score", "is_novel", "similar_content", "uniqueness_factors")

    def __init__(self) -> None:
        self.novelty_score = 0.0
        self.is_novel = True
        self.similar_content: List[str] = []
        self.uniqueness_factors: List[str] = []

    def to_dict(self) -> Dict:
        return {"novelty_score": round(self.novelty_score, 3), "is_novel": self.is_novel,
                "similar_count": len(self.similar_content), "uniqueness_factors": list(self.uniqueness_factors)}


class NoveltyDetector:
    def __init__(self, threshold: float = 0.7):
        self._threshold = threshold
        self._seen_hashes: set = set()

    def detect(self, content: str, existing: Optional[List[str]] = None) -> NoveltyResult:
        result = NoveltyResult()
        content_hash = hashlib.sha256(content.lower().strip().encode()).hexdigest()
        if content_hash in self._seen_hashes:
            result.novelty_score = 0.0
            result.is_novel = False
            return result
        self._seen_hashes.add(content_hash)

        if existing:
            words = set(content.lower().split())
            for ex in existing:
                ex_words = set(ex.lower().split())
                overlap = len(words & ex_words) / max(len(words | ex_words), 1)
                if overlap > self._threshold:
                    result.similar_content.append(ex[:50])

        result.novelty_score = max(0.0, 1.0 - len(result.similar_content) * 0.2)
        result.is_novel = result.novelty_score > 0.5
        if result.is_novel:
            result.uniqueness_factors.append("No similar content found")
        return result
