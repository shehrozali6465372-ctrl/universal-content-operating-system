"""
Embedding Engine — Sprint 3 (v3.0)

Lightweight TF-IDF based semantic similarity without external ML libraries.

Public API:
    embed(text) -> List[float]
    similarity(text_a, text_b) -> float
    cross_similarity(texts) -> List[List[float]]
    cosine_similarity(vec_a, vec_b) -> float

Features:
    - TF-IDF vectorization
    - Cosine similarity
    - Cross-document similarity matrix
    - Vocabulary building from corpus
    - Dimensionality reduction (top features)
    - Normalized embeddings

Version: 3.0.0
"""

from __future__ import annotations

import re
import math
from collections import Counter
from typing import Dict, List, Set


# Stop words (same as SemanticAnalyzer)
_STOP_WORDS: Set[str] = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "out", "off", "over",
    "under", "again", "further", "then", "once", "here", "there",
    "when", "where", "why", "how", "all", "both", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "just", "because", "but", "and",
    "or", "if", "while", "that", "this", "it", "its", "he", "she",
    "they", "them", "we", "you", "i", "me", "my", "your", "his", "her",
    "our", "their", "what", "which", "who", "whom", "am", "about", "up",
    "down", "also", "like", "well", "much", "many", "even", "still",
    "really", "quite", "right", "now", "new", "one", "two", "get", "got",
    "make", "made", "go", "going", "come", "came", "see", "know", "take",
    "want", "give", "use", "find", "tell", "ask", "work", "seem", "feel",
    "try", "leave", "call", "need", "become", "keep", "let", "begin",
    "show", "hear", "play", "run", "move", "live", "believe", "bring",
    "happen", "must", "ka", "ki", "ke", "hai", "ho", "ko", "se", "ne",
    "mein", "par", "ya", "aur", "bhi", "kya", "kab", "kaise", "kyun",
}


class EmbeddingEngine:
    """Lightweight TF-IDF based embedding engine.

    Usage::

        engine = EmbeddingEngine(vocab_size=500)
        engine.fit(corpus)
        vec = engine.embed("AI is transforming technology")
        sim = engine.similarity("AI jobs", "artificial intelligence careers")
    """

    def __init__(self, vocab_size: int = 500) -> None:
        """
        Args:
            vocab_size: Maximum vocabulary size to keep (top features).
        """
        self.vocab_size = vocab_size
        self._vocab: Dict[str, int] = {}
        self._idf: Dict[str, float] = {}
        self._fitted = False

    def fit(self, corpus: List[str]) -> None:
        """Build vocabulary and IDF from a corpus of texts.

        Args:
            corpus: List of text strings to build vocabulary from.
        """
        doc_freq: Counter = Counter()
        term_freq: Counter = Counter()
        n_docs = len(corpus)

        for text in corpus:
            words = self._tokenize(text)
            unique_words = set(words)
            for w in unique_words:
                doc_freq[w] += 1
            for w in words:
                term_freq[w] += 1

        # Select top vocab_size terms by frequency
        top_terms = term_freq.most_common(self.vocab_size)
        self._vocab = {term: idx for idx, (term, _) in enumerate(top_terms)}

        # Compute IDF: log(N / df)
        for term in self._vocab:
            df = doc_freq.get(term, 0)
            self._idf[term] = math.log((n_docs + 1) / (df + 1)) + 1.0

        self._fitted = True

    def embed(self, text: str) -> List[float]:
        """Convert text to a TF-IDF vector.

        Returns a list of floats representing the embedding.
        If not fitted, returns an empty list.
        """
        if not self._fitted or not self._vocab:
            return []

        words = self._tokenize(text)
        if not words:
            return [0.0] * len(self._vocab)

        tf = Counter(words)
        total = len(words)

        vector = [0.0] * len(self._vocab)
        for word, count in tf.items():
            if word in self._vocab:
                idx = self._vocab[word]
                tf_val = count / total
                idf_val = self._idf.get(word, 1.0)
                vector[idx] = tf_val * idf_val

        return self._normalize(vector)

    def similarity(self, text_a: str, text_b: str) -> float:
        """Compute cosine similarity between two texts.

        Returns a value between 0.0 (no similarity) and 1.0 (identical).
        """
        vec_a = self.embed(text_a)
        vec_b = self.embed(text_b)

        if not vec_a or not vec_b:
            return 0.0

        return self.cosine_similarity(vec_a, vec_b)

    def cross_similarity(self, texts: List[str]) -> List[List[float]]:
        """Compute pairwise similarity matrix for a list of texts.

        Returns an NxN matrix where matrix[i][j] = similarity(texts[i], texts[j]).
        """
        embeddings = [self.embed(t) for t in texts]
        n = len(texts)
        matrix: List[List[float]] = []

        for i in range(n):
            row: List[float] = []
            for j in range(n):
                if i == j:
                    row.append(1.0)
                else:
                    row.append(self.cosine_similarity(embeddings[i], embeddings[j]))
            matrix.append(row)

        return matrix

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(vec_a) != len(vec_b) or not vec_a:
            return 0.0

        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        mag_a = math.sqrt(sum(a * a for a in vec_a))
        mag_b = math.sqrt(sum(b * b for b in vec_b))

        if mag_a == 0.0 or mag_b == 0.0:
            return 0.0

        return round(dot / (mag_a * mag_b), 4)

    def get_vocabulary(self) -> List[str]:
        """Get the current vocabulary."""
        return list(self._vocab.keys())

    def get_vocab_size(self) -> int:
        return len(self._vocab)

    def is_fitted(self) -> bool:
        return self._fitted

    def reset(self) -> None:
        """Reset the engine."""
        self._vocab.clear()
        self._idf.clear()
        self._fitted = False

    def _tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r"[a-zA-Z0-9\u0600-\u06FF]+", text.lower())
        return [t for t in tokens if len(t) >= 2 and t not in _STOP_WORDS]

    def _normalize(self, vector: List[float]) -> List[float]:
        """L2 normalize a vector."""
        mag = math.sqrt(sum(x * x for x in vector))
        if mag == 0.0:
            return vector
        return [round(x / mag, 6) for x in vector]
