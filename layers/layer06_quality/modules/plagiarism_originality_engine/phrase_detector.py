"""Phrase Detector — Detect repeated and near-duplicate phrases in content.

Checks:
- Exact phrase repetition (same phrase appearing multiple times)
- N-gram similarity (consecutive word sequences)
- Common phrase detection (overused idioms/cliches)
"""
from __future__ import annotations
import re
from collections import Counter
from typing import Dict, List, Tuple

from layers.layer06_quality.modules.plagiarism_originality_engine.originality_report import FlaggedSegment


COMMON_CLICHES = {
    "at the end of the day",
    "in this day and age",
    "it goes without saying",
    "needless to say",
    "the fact of the matter",
    "for all intents and purposes",
    "when all is said and done",
    "on a daily basis",
    "in the grand scheme of things",
    "to be honest",
    "as a matter of fact",
    "in my humble opinion",
    "the bottom line is",
    "it is worth noting",
    "to sum up",
    "in conclusion",
    "first and foremost",
    "last but not least",
    "time will tell",
    "easier said than done",
}

_stop_words = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "and", "but", "or", "if", "this", "that", "these", "those", "it",
    "its", "not", "no", "so", "than", "too", "very", "just",
}


class PhraseDetector:
    """Detect repeated and overused phrases in content."""

    def __init__(
        self,
        min_phrase_length: int = 3,
        max_phrase_length: int = 12,
        repeat_threshold: int = 2,
    ) -> None:
        self._min_phrase = min_phrase_length
        self._max_phrase = max_phrase_length
        self._repeat_threshold = repeat_threshold
        self._check_count = 0

    def detect_exact_repeats(self, text: str) -> List[FlaggedSegment]:
        """Detect exact repeated phrases."""
        flags: List[FlaggedSegment] = []
        sentences = self._split_sentences(text)
        seen_phrases: Dict[str, List[Tuple[str, int]]] = {}

        for n in range(self._min_phrase, min(self._max_phrase + 1, 8)):
            for sentence in sentences:
                words = sentence.split()
                for i in range(len(words) - n + 1):
                    phrase = " ".join(words[i:i + n]).lower()
                    if any(w in _stop_words for w in words[i:i + n]):
                        continue
                    if phrase not in seen_phrases:
                        seen_phrases[phrase] = []
                    pos = text.lower().find(phrase)
                    seen_phrases[phrase].append((sentence, pos))

        for phrase, occurrences in seen_phrases.items():
            if len(occurrences) >= self._repeat_threshold:
                flags.append(FlaggedSegment(
                    text=phrase,
                    start_pos=occurrences[0][1],
                    end_pos=occurrences[0][1] + len(phrase),
                    match_type="exact_repeat",
                    similarity_score=1.0,
                    source="internal",
                    severity="medium",
                    suggestion=f"Phrase '{phrase}' repeated {len(occurrences)} times — rephrase for variety",
                ))

        self._check_count += 1
        return flags

    def detect_cliches(self, text: str) -> List[FlaggedSegment]:
        """Detect common cliches and overused phrases."""
        flags: List[FlaggedSegment] = []
        text_lower = text.lower()

        for cliche in COMMON_CLICHES:
            if cliche in text_lower:
                pos = text_lower.find(cliche)
                flags.append(FlaggedSegment(
                    text=cliche,
                    start_pos=pos,
                    end_pos=pos + len(cliche),
                    match_type="cliche",
                    similarity_score=0.9,
                    source="cliche_database",
                    severity="low",
                    suggestion=f"Consider replacing cliché '{cliche}' with original language",
                ))

        self._check_count += 1
        return flags

    def detect_ngram_duplicates(self, text: str, n: int = 4) -> List[FlaggedSegment]:
        """Detect repeated n-grams."""
        flags: List[FlaggedSegment] = []
        words = [w.lower() for w in text.split() if w.isalpha()]
        ngrams: Counter = Counter()

        for i in range(len(words) - n + 1):
            gram = tuple(words[i:i + n])
            ngrams[gram] += 1

        for gram, count in ngrams.items():
            if count >= self._repeat_threshold and len(gram) >= 3:
                phrase = " ".join(gram)
                pos = text.lower().find(phrase)
                flags.append(FlaggedSegment(
                    text=phrase,
                    start_pos=pos,
                    end_pos=pos + len(phrase),
                    match_type="ngram_repeat",
                    similarity_score=0.85,
                    source="internal",
                    severity="low" if count == 2 else "medium",
                    suggestion=f"N-gram '{phrase}' appears {count} times — diversify language",
                ))

        self._check_count += 1
        return flags

    def _split_sentences(self, text: str) -> List[str]:
        return [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]

    @property
    def check_count(self) -> int:
        return self._check_count
