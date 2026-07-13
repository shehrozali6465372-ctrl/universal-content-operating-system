"""
Semantic Search
Layer 2: Research Engine — Module 7

Word embedding-free semantic search:
- TF-IDF style relevance scoring
- Query expansion
- Faceted search
- Result ranking
"""

import math
from collections import Counter, defaultdict
from typing import Dict, List, Optional

_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "and", "but", "or", "if",
    "this", "that", "it", "not", "no", "so", "very", "just",
}


class SearchResult:
    """A single search result with relevance score."""

    __slots__ = ("entry_id", "relevance_score", "matched_terms", "match_type")

    def __init__(self, entry_id: str, relevance_score: float = 0.0,
                 matched_terms: Optional[List[str]] = None, match_type: str = "text"):
        self.entry_id = entry_id
        self.relevance_score = max(0.0, min(1.0, relevance_score))
        self.matched_terms = matched_terms or []
        self.match_type = match_type

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "relevance_score": self.relevance_score,
            "matched_terms": self.matched_terms,
            "match_type": self.match_type,
        }


class SemanticSearch:
    """TF-IDF inspired semantic search engine."""

    def __init__(self, idf_data: Optional[Dict[str, float]] = None):
        self._idf: Dict[str, float] = idf_data or {}
        self._doc_count = 0

    def update_idf(self, documents: List[List[str]]):
        """Update IDF values from a corpus of tokenized documents."""
        self._doc_count = len(documents)
        df: Dict[str, int] = defaultdict(int)
        for doc in documents:
            unique_words = set(w.lower() for w in doc if w.lower() not in _STOP_WORDS)
            for word in unique_words:
                df[word] += 1
        self._idf = {
            word: math.log(self._doc_count / count) + 1
            for word, count in df.items()
        }

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        import re
        return [w.lower() for w in re.findall(r'\b[a-zA-Z]{2,}\b', text) if w.lower() not in _STOP_WORDS]

    def _tf(self, tokens: List[str]) -> Dict[str, float]:
        """Term frequency."""
        counter = Counter(tokens)
        total = len(tokens) if tokens else 1
        return {word: count / total for word, count in counter.items()}

    def _tfidf(self, tokens: List[str]) -> Dict[str, float]:
        """TF-IDF vector."""
        tf = self._tf(tokens)
        return {
            word: tf_val * self._idf.get(word, 1.0)
            for word, tf_val in tf.items()
        }

    def _cosine_similarity(self, vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        """Cosine similarity between two TF-IDF vectors."""
        common = set(vec_a.keys()) & set(vec_b.keys())
        if not common:
            return 0.0
        dot = sum(vec_a[w] * vec_b[w] for w in common)
        norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
        norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(
        self,
        query: str,
        documents: Dict[str, str],
        max_results: int = 10,
    ) -> List[SearchResult]:
        """Search documents by query."""
        query_tokens = self._tokenize(query)
        query_vec = self._tfidf(query_tokens)

        results = []
        for doc_id, doc_text in documents.items():
            doc_tokens = self._tokenize(doc_text)
            doc_vec = self._tfidf(doc_tokens)
            sim = self._cosine_similarity(query_vec, doc_vec)
            if sim > 0:
                matched = [t for t in query_tokens if t in set(doc_tokens)]
                results.append(SearchResult(doc_id, sim, matched, "semantic"))

        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:max_results]

    def expand_query(self, query: str, related_terms: Optional[List[str]] = None) -> str:
        """Expand query with related terms."""
        if not related_terms:
            return query
        expansion = " ".join(related_terms[:3])
        return f"{query} {expansion}"

    def get_idf(self, term: str) -> float:
        return self._idf.get(term.lower(), 1.0)
