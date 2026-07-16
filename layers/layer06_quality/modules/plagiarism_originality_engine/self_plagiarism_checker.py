"""Self-Plagiarism Checker — Detect content reuse from previously published material.

Maintains a history of published content and checks new content against it.
"""
from __future__ import annotations
import re
from typing import Dict, List

from layers.layer06_quality.modules.plagiarism_originality_engine.originality_report import SelfPlagiarismMatch


_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "and", "but", "or", "if", "this", "that", "these", "those", "it",
    "its", "not", "no", "so", "than", "too", "very", "just",
}


class SelfPlagiarismChecker:
    """Check new content against previously published content."""

    def __init__(self, similarity_threshold: float = 0.6) -> None:
        self._threshold = max(0.0, min(1.0, similarity_threshold))
        self._published_history: List[Dict[str, str]] = []
        self._check_count = 0

    def add_published(self, content: str, source: str = "") -> None:
        """Add content to published history."""
        self._published_history.append({
            "content": content,
            "source": source,
        })

    def check(self, new_content: str) -> List[SelfPlagiarismMatch]:
        """Check new content against published history."""
        matches: List[SelfPlagiarismMatch] = []
        new_words = set(self._extract_words(new_content))

        for entry in self._published_history:
            prev_words = set(self._extract_words(entry["content"]))
            similarity = self._jaccard_similarity(new_words, prev_words)

            if similarity >= self._threshold:
                match_type = "exact" if similarity > 0.9 else "near_duplicate"
                matches.append(SelfPlagiarismMatch(
                    current_text=new_content[:200],
                    previous_text=entry["content"][:200],
                    previous_source=entry.get("source", "unknown"),
                    similarity_score=similarity,
                    match_type=match_type,
                ))

            # Also check sentence-level matches
            sentence_matches = self._check_sentences(new_content, entry["content"])
            for sm in sentence_matches:
                sm.previous_source = entry.get("source", "unknown")
                matches.append(sm)

        self._check_count += 1
        return matches

    def check_batch(self, contents: List[str]) -> List[List[SelfPlagiarismMatch]]:
        """Check multiple contents against history."""
        return [self.check(c) for c in contents]

    def get_high_similarity(self, matches: List[SelfPlagiarismMatch]) -> List[SelfPlagiarismMatch]:
        """Return only high-similarity matches."""
        return [m for m in matches if m.similarity_score >= 0.8]

    def clear_history(self) -> None:
        """Clear published content history."""
        self._published_history.clear()

    @property
    def history_size(self) -> int:
        return len(self._published_history)

    def _extract_words(self, text: str) -> List[str]:
        """Extract meaningful words from text."""
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return [w for w in words if w not in _STOP_WORDS]

    def _jaccard_similarity(self, set_a: set, set_b: set) -> float:
        """Jaccard similarity between two word sets."""
        if not set_a or not set_b:
            return 0.0
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union) if union else 0.0

    def _check_sentences(
        self, new_text: str, prev_text: str,
    ) -> List[SelfPlagiarismMatch]:
        """Check for sentence-level duplicates."""
        matches: List[SelfPlagiarismMatch] = []
        new_sentences = [s.strip() for s in re.split(r'[.!?]+', new_text) if len(s.strip()) > 15]
        prev_sentences = [s.strip() for s in re.split(r'[.!?]+', prev_text) if len(s.strip()) > 15]

        for ns in new_sentences:
            ns_words = set(ns.lower().split())
            for ps in prev_sentences:
                ps_words = set(ps.lower().split())
                sim = self._jaccard_similarity(ns_words, ps_words)
                if sim >= 0.75:
                    matches.append(SelfPlagiarismMatch(
                        current_text=ns[:200],
                        previous_text=ps[:200],
                        similarity_score=sim,
                        match_type="sentence_duplicate",
                    ))
                    break  # One match per new sentence is enough

        return matches

    @property
    def check_count(self) -> int:
        return self._check_count
