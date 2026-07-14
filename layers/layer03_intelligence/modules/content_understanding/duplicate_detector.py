"""
Duplicate Meaning Detector — Sprint 4 (v4.0)

Detects texts with different wording but same meaning.

Public API:
    detect(text_a, text_b) -> DuplicateResult
    find_duplicates(texts, threshold) -> List[Tuple[int, int]]
    deduplicate(texts, threshold) -> List[str]
    get_groups(texts, threshold) -> List[List[int]]

Version: 4.0.0
"""

from __future__ import annotations
import re
from typing import Dict, List, Set, Tuple


# Semantic equivalence groups
_SYNONYM_GROUPS: List[Set[str]] = [
    {"artificial_intelligence", "ai", "machine_intelligence", "neural_computation", "deep_learning", "machine_learning", "neural_network", "llm", "gpt", "chatgpt", "openai", "generative_ai"},
    {"increase", "rise", "grow", "boost", "surge", "expand"},
    {"decrease", "decline", "fall", "drop", "reduce", "shrink"},
    {"good", "great", "excellent", "wonderful", "fantastic", "superb"},
    {"bad", "terrible", "horrible", "awful", "dreadful", "poor"},
    {"fast", "quick", "rapid", "swift", "speedy"},
    {"slow", "sluggish", "gradual", "leisurely"},
    {"buy", "purchase", "acquire", "obtain"},
    {"sell", "trade", "market", "offer"},
    {"job", "career", "position", "role", "employment", "work"},
    {"company", "corporation", "firm", "business", "enterprise", "organization"},
    {"money", "cash", "funds", "capital", "finance"},
    {"help", "assist", "support", "aid"},
    {"big", "large", "huge", "massive", "enormous"},
    {"small", "tiny", "little", "miniature"},
    {"smart", "intelligent", "clever", "bright", "brilliant"},
    {"learn", "study", "acquire knowledge", "educate"},
    {"teach", "instruct", "educate", "train", "mentor"},
    {"amazing", "wonderful", "incredible", "remarkable", "awesome"},
    {"technology", "tech", "digital", "computing"},
    {"career", "job", "profession", "occupation"},
    {"salary", "wage", "income", "pay", "compensation"},
    {"tool", "utility", "software", "application", "app"},
    {"problem", "issue", "challenge", "difficulty"},
    {"solution", "fix", "remedy", "answer"},
    {"future", "upcoming", "coming", "next"},
    {"trend", "pattern", "movement", "shift"},
    {"data", "information", "content", "facts"},
]

# Build reverse lookup
_SYNONYM_MAP: Dict[str, Set[str]] = {}
for group in _SYNONYM_GROUPS:
    for word in group:
        _SYNONYM_MAP[word] = group - {word}


class DuplicateResult:
    """Result of duplicate meaning detection."""

    __slots__ = ("text_a", "text_b", "is_duplicate", "similarity",
                 "synonym_matches", "explanation")

    def __init__(self) -> None:
        self.text_a: str = ""
        self.text_b: str = ""
        self.is_duplicate: bool = False
        self.similarity: float = 0.0
        self.synonym_matches: List[Tuple[str, str]] = []
        self.explanation: str = ""

    def to_dict(self) -> Dict:
        return {
            "text_a": self.text_a,
            "text_b": self.text_b,
            "is_duplicate": self.is_duplicate,
            "similarity": round(self.similarity, 3),
            "synonym_matches": [(a, b) for a, b in self.synonym_matches],
            "explanation": self.explanation,
        }


class DuplicateDetector:
    """Detects texts with different wording but same meaning.

    Usage::

        detector = DuplicateDetector()
        r = detector.detect("AI is amazing", "artificial intelligence is wonderful")
        print(r.is_duplicate, r.similarity)
    """

    def __init__(self, synonym_boost: float = 0.6) -> None:
        self._synonym_map = dict(_SYNONYM_MAP)
        self._synonym_boost = synonym_boost

    def detect(self, text_a: str, text_b: str) -> DuplicateResult:
        """Detect if two texts have the same meaning."""
        result = DuplicateResult()
        result.text_a = text_a
        result.text_b = text_b

        if not text_a or not text_b:
            return result

        words_a = set(self._tokenize(text_a))
        words_b = set(self._tokenize(text_b))

        # 1. Exact word overlap
        exact_overlap = words_a & words_b
        exact_score = len(exact_overlap) / max(len(words_a | words_b), 1)

        # 2. Synonym matches (bidirectional + word-level)
        synonym_matches: List[Tuple[str, str]] = []
        seen_pairs: Set[Tuple[str, str]] = set()
        for wa in words_a:
            synonyms_a = self._synonym_map.get(wa, set())
            wa_words = set(wa.replace("_", " ").split())
            for wb in words_b:
                synonyms_b = self._synonym_map.get(wb, set())
                wb_words = set(wb.replace("_", " ").split())
                # Direct match or word-level overlap
                direct_match = wb in synonyms_a or wa in synonyms_b
                word_match = bool(wa_words & wb_words) and wa != wb
                if direct_match or word_match:
                    pair = (min(wa, wb), max(wa, wb))
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        synonym_matches.append((wa, wb))

        synonym_score = len(synonym_matches) / max(len(words_a | words_b), 1) * self._synonym_boost

        # 3. Multi-word phrase matching (check if full text contains phrase from synonym groups)
        phrase_matches = 0
        text_a_lower = text_a.lower()
        text_b_lower = text_b.lower()
        all_phrases = set()
        for group in _SYNONYM_GROUPS:
            for phrase in group:
                if " " in phrase:
                    all_phrases.add(phrase)
        for phrase in all_phrases:
            if phrase in text_a_lower and phrase in text_b_lower:
                phrase_matches += 1
            elif phrase in text_a_lower:
                for other in all_phrases:
                    if other != phrase and other in text_b_lower:
                        phrase_matches += 1
                        break
            elif phrase in text_b_lower:
                for other in all_phrases:
                    if other != phrase and other in text_a_lower:
                        phrase_matches += 1
                        break

        phrase_score = phrase_matches / max(len(words_a | words_b), 1) * 0.4

        # 4. Combined score
        total = min(1.0, exact_score + synonym_score + phrase_score)
        result.similarity = round(total, 3)
        result.is_duplicate = total >= 0.20
        result.synonym_matches = synonym_matches

        if result.is_duplicate:
            match_str = ", ".join(f"'{a}'≈'{b}'" for a, b in synonym_matches[:3])
            result.explanation = (
                f"Meaning similarity: {total:.1%}. "
                f"Exact overlap: {len(exact_overlap)} words. "
                f"Synonym matches: {match_str or 'none'}"
            )

        return result

    def find_duplicates(self, texts: List[str], threshold: float = 0.3) -> List[Tuple[int, int]]:
        """Find indices of duplicate text pairs."""
        duplicates: List[Tuple[int, int]] = []
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                r = self.detect(texts[i], texts[j])
                if r.is_duplicate and r.similarity >= threshold:
                    duplicates.append((i, j))
        return duplicates

    def deduplicate(self, texts: List[str], threshold: float = 0.3) -> List[str]:
        """Remove duplicate texts, keeping the first occurrence."""
        keep: List[str] = []
        for text in texts:
            is_dup = False
            for kept in keep:
                r = self.detect(text, kept)
                if r.is_duplicate and r.similarity >= threshold:
                    is_dup = True
                    break
            if not is_dup:
                keep.append(text)
        return keep

    def get_groups(self, texts: List[str], threshold: float = 0.3) -> List[List[int]]:
        """Group texts by meaning similarity."""
        groups: List[List[int]] = []
        assigned: Set[int] = set()

        for i in range(len(texts)):
            if i in assigned:
                continue
            group = [i]
            assigned.add(i)
            for j in range(i + 1, len(texts)):
                if j in assigned:
                    continue
                r = self.detect(texts[i], texts[j])
                if r.is_duplicate and r.similarity >= threshold:
                    group.append(j)
                    assigned.add(j)
            groups.append(group)

        return groups

    def add_synonym_group(self, words: Set[str]) -> None:
        """Add a custom synonym group."""
        for word in words:
            existing = self._synonym_map.get(word, set())
            existing.update(words - {word})
            self._synonym_map[word] = existing

    _FORM_MAP: Dict[str, str] = {
        "increasing": "increase", "decreasing": "decrease",
        "declining": "decline", "rising": "rise", "falling": "fall",
        "growing": "grow", "shrinking": "shrink", "boosting": "boost",
        "improving": "improve", "worsening": "worsen", "reducing": "reduce",
        "surging": "surge", "expanding": "expand", "dropping": "drop",
        "winning": "win", "losing": "lose", "succeeding": "succeed",
        "failing": "fail", "loving": "love", "hating": "hate",
        "increases": "increase", "decreases": "decrease",
        "declines": "decline", "rises": "rise", "falls": "fall",
        "grows": "grow", "shrinks": "shrink", "boosts": "boost",
        "improves": "improve", "worsens": "worsen", "reduces": "reduce",
        "surges": "surge", "expands": "expand", "drops": "drop",
        "amazing": "amazing", "wonderful": "wonderful",
        "artificial": "artificial", "intelligence": "intelligence",
    }

    @staticmethod
    def _lemmatize(word: str) -> str:
        w = word.lower()
        if w in DuplicateDetector._FORM_MAP:
            return DuplicateDetector._FORM_MAP[w]
        for suffix, replacement in [
            ("ization", "ize"), ("isation", "ise"),
            ("fulness", "ful"), ("ousness", "ous"),
            ("ments", "ment"), ("ating", "ate"),
            ("ying", "y"), ("ing", ""), ("ness", ""),
            ("ment", ""), ("able", ""), ("ible", ""),
            ("tion", "t"), ("sion", "s"),
            ("ally", "al"), ("ely", "e"), ("ily", "y"),
            ("ies", "y"), ("ves", "f"),
            ("ated", "ate"), ("ened", "e"),
            ("ized", "ize"), ("ised", "ise"),
            ("less", ""), ("ful", ""),
            ("ous", ""), ("ive", ""),
            ("ers", "er"), ("est", ""),
            ("er", ""), ("ed", ""),
            ("ly", ""),
            ("s", ""),
        ]:
            if w.endswith(suffix) and len(w) - len(suffix) >= 3:
                base = w[:-len(suffix)] + replacement
                if len(base) >= 3:
                    return base
        return w

    # Map abbreviations/synonyms to normalized forms for better matching
    _NORMALIZE_MAP: Dict[str, str] = {
        "ai": "artificial_intelligence",
        "ml": "machine_learning",
        "dl": "deep_learning",
        "llm": "large_language_model",
        "gpt": "generative_pretrained_transformer",
    }

    def _tokenize(self, text: str) -> List[str]:
        stop = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                "have", "has", "had", "do", "does", "did", "will", "would",
                "could", "should", "may", "might", "can", "to", "of", "in",
                "for", "on", "with", "at", "by", "from", "as", "and", "or",
                "but", "not", "this", "that", "it", "its", "very", "just"}
        tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
        result = []
        for t in tokens:
            if len(t) < 2 or t in stop:
                continue
            normalized = self._NORMALIZE_MAP.get(t, self._lemmatize(t))
            result.append(normalized)
        return result
