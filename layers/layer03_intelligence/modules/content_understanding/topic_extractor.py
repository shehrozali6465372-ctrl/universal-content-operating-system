"""
Topic Extractor
Extracts topics from text using TF-IDF style keyword scoring and clustering.
"""

from collections import Counter
from typing import Dict, List, Set


# Common stop words
STOP_WORDS: Set[str] = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "just",
    "because", "but", "and", "or", "if", "while", "that", "this",
    "it", "its", "he", "she", "they", "them", "we", "you", "i", "me",
    "my", "your", "his", "her", "our", "their", "what", "which", "who",
}


class TopicExtractor:
    """Extracts topics from text using keyword frequency analysis."""

    def __init__(self, min_word_length: int = 3, max_topics: int = 10):
        self.min_word_length = min_word_length
        self.max_topics = max_topics

    def extract(self, text: str) -> List[Dict]:
        """Extract topics from text.

        Returns list of dicts: [{"topic": str, "score": float, "frequency": int}]
        """
        words = self._tokenize(text)
        if not words:
            return []

        freq = Counter(words)
        total = len(words)

        topics = []
        for word, count in freq.most_common(self.max_topics * 2):
            # TF score: frequency relative to document
            tf = count / total
            # Boost multi-character words
            length_bonus = min(1.5, len(word) / 5.0)
            score = round(tf * length_bonus, 4)
            topics.append({"topic": word, "score": score, "frequency": count})

        # Sort by score, take top N
        topics.sort(key=lambda x: -x["score"])
        return topics[:self.max_topics]

    def extract_multi_word(self, text: str, window: int = 2) -> List[Dict]:
        """Extract multi-word topic phrases using sliding window."""
        words = self._tokenize(text)
        if len(words) < window:
            return []

        phrases: Counter = Counter()
        for i in range(len(words) - window + 1):
            phrase = " ".join(words[i:i + window])
            phrases[phrase] += 1

        result = []
        for phrase, count in phrases.most_common(self.max_topics):
            score = round(count / max(len(words) - window + 1, 1), 4)
            result.append({"topic": phrase, "score": score, "frequency": count})

        return result

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into meaningful words."""
        words = text.lower().split()
        return [
            w.strip(".,!?;:\"'()-")
            for w in words
            if (
                len(w.strip(".,!?;:\"'()-")) >= self.min_word_length
                and w.strip(".,!?;:\"'()-") not in STOP_WORDS
            )
        ]
