"""Originality Scorer — Score content originality based on multiple signals.

Signals:
- Vocabulary diversity
- Sentence structure variety
- Unique idea density
- Phrase uniqueness
- Content freshness indicators
"""
from __future__ import annotations
import re
from typing import Dict



class OriginalityScorer:
    """Score content originality using multiple linguistic signals."""

    def __init__(self) -> None:
        self._check_count = 0

    def score(self, text: str) -> Dict[str, float]:
        """Calculate originality score components."""
        signals: Dict[str, float] = {}
        signals["vocabulary_diversity"] = self._vocabulary_diversity(text)
        signals["sentence_variety"] = self._sentence_variety(text)
        signals["unique_ideas"] = self._unique_ideas_density(text)
        signals["phrase_uniqueness"] = self._phrase_uniqueness(text)
        signals["structural_variety"] = self._structural_variety(text)
        self._check_count += 1
        return signals

    def get_overall_score(self, signals: Dict[str, float]) -> float:
        """Combine signals into a single originality score."""
        if not signals:
            return 0.5
        weights = {
            "vocabulary_diversity": 0.25,
            "sentence_variety": 0.20,
            "unique_ideas": 0.25,
            "phrase_uniqueness": 0.15,
            "structural_variety": 0.15,
        }
        total = 0.0
        weight_sum = 0.0
        for key, weight in weights.items():
            if key in signals:
                total += signals[key] * weight
                weight_sum += weight
        return round(total / weight_sum if weight_sum > 0 else 0.5, 3)

    def _vocabulary_diversity(self, text: str) -> float:
        """Type-token ratio (unique words / total words)."""
        words = [w.lower() for w in text.split() if w.isalpha() and len(w) > 1]
        if not words:
            return 0.0
        unique = len(set(words))
        ratio = unique / len(words)
        return min(1.0, ratio * 1.2)  # Slight boost for natural text

    def _sentence_variety(self, text: str) -> float:
        """Measure sentence length variation."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) < 2:
            return 0.5
        lengths = [len(s.split()) for s in sentences]
        avg = sum(lengths) / len(lengths)
        if avg == 0:
            return 0.0
        variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
        cv = (variance ** 0.5) / avg if avg > 0 else 0
        return min(1.0, cv * 1.5)

    def _unique_ideas_density(self, text: str) -> float:
        """Estimate density of unique content-bearing words."""
        content_words = [
            w.lower() for w in text.split()
            if w.isalpha() and len(w) > 3 and w.lower() not in _stop_words
        ]
        if not content_words:
            return 0.3
        unique = len(set(content_words))
        return min(1.0, unique / max(1, len(content_words)))

    def _phrase_uniqueness(self, text: str) -> float:
        """Estimate how unique the phrases are."""
        words = [w.lower() for w in text.split() if w.isalpha()]
        if len(words) < 4:
            return 0.5
        bigrams = set()
        for i in range(len(words) - 1):
            bigrams.add((words[i], words[i + 1]))
        common_bigrams = sum(
            1 for b in bigrams
            if b[0] in _stop_words and b[1] in _stop_words
        )
        total = len(bigrams) if bigrams else 1
        unique_ratio = 1.0 - (common_bigrams / total)
        return max(0.0, min(1.0, unique_ratio))

    def _structural_variety(self, text: str) -> float:
        """Measure variety in text structure."""
        score = 0.5
        # Has paragraphs
        if "\n\n" in text:
            score += 0.15
        # Has lists
        if re.search(r'^\s*[-*•]\s', text, re.MULTILINE):
            score += 0.1
        # Has headings
        if re.search(r'^#+\s', text, re.MULTILINE):
            score += 0.1
        # Has numbers/stats
        if re.search(r'\d+', text):
            score += 0.05
        # Has quotes
        if '"' in text or '"' in text:
            score += 0.1
        return min(1.0, score)


# Module-level stop words for _unique_ideas_density
_stop_words = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "and", "but", "or", "if", "this", "that", "these", "those", "it",
    "its", "not", "no", "so", "than", "too", "very", "just", "also",
    "about", "which", "who", "whom", "when", "where", "how", "what",
    "there", "here", "then", "now", "only", "more", "most", "some",
    "any", "all", "each", "every", "both", "few", "many", "much",
}
