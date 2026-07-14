"""
Keyword Analyzer
Analyzes keywords for relevance, density, and distribution.
"""

from collections import Counter
from typing import Dict, List


# Domain-specific keyword weights
DOMAIN_WEIGHTS: Dict[str, Dict[str, float]] = {
    "technology": {"ai": 2.0, "software": 1.5, "data": 1.5, "digital": 1.3, "tech": 1.5},
    "finance": {"invest": 2.0, "money": 1.5, "stock": 1.5, "crypto": 1.8, "finance": 2.0},
    "health": {"health": 2.0, "medical": 1.5, "fitness": 1.5, "wellness": 1.3, "diet": 1.2},
    "education": {"learn": 2.0, "course": 1.5, "study": 1.5, "skill": 1.3, "training": 1.2},
    "general": {},
}


class KeywordAnalysis:
    """Result of keyword analysis."""

    __slots__ = ("keywords", "density", "primary_keywords", "secondary_keywords", "score")

    def __init__(self):
        self.keywords: List[Dict] = []
        self.density = 0.0
        self.primary_keywords: List[str] = []
        self.secondary_keywords: List[str] = []
        self.score = 0.0

    def to_dict(self) -> dict:
        return {
            "keywords": self.keywords[:10],
            "density": self.density,
            "primary_keywords": self.primary_keywords,
            "secondary_keywords": self.secondary_keywords,
            "score": self.score,
        }


class KeywordAnalyzer:
    """Analyzes keywords in text for relevance and quality."""

    def __init__(self, max_keywords: int = 20):
        self.max_keywords = max_keywords
        self._domain_weights = dict(DOMAIN_WEIGHTS)

    def analyze(self, text: str, domain: str = "general") -> KeywordAnalysis:
        """Analyze keywords in text for a given domain."""
        words = text.lower().split()
        total_words = len(words)
        if total_words == 0:
            return KeywordAnalysis()

        freq = Counter(words)
        weights = self._domain_weights.get(domain, self._domain_weights["general"])

        result = KeywordAnalysis()
        for word, count in freq.most_common(self.max_keywords):
            base_density = count / total_words
            weight = weights.get(word, 1.0)
            relevance = round(base_density * weight * 100, 3)
            result.keywords.append({
                "keyword": word,
                "frequency": count,
                "density": round(base_density, 4),
                "weight": weight,
                "relevance": relevance,
            })

        # Calculate overall density (unique keyword coverage)
        unique_keywords = len(freq)
        result.density = round(unique_keywords / max(total_words, 1), 3)

        # Primary = top 3, Secondary = next 5
        sorted_kw = sorted(result.keywords, key=lambda x: -x["relevance"])
        result.primary_keywords = [k["keyword"] for k in sorted_kw[:3]]
        result.secondary_keywords = [k["keyword"] for k in sorted_kw[3:8]]

        # Overall score
        if result.keywords:
            result.score = round(
                sum(k["relevance"] for k in result.keywords[:5]) / 5, 3
            )

        return result

    def analyze_batch(self, texts: List[str], domain: str = "general") -> List[KeywordAnalysis]:
        """Analyze keywords for multiple texts."""
        return [self.analyze(t, domain) for t in texts]

    def get_common_keywords(self, texts: List[str], top_n: int = 10) -> List[Dict]:
        """Find keywords common across multiple texts."""
        all_words: Counter = Counter()
        for text in texts:
            words = set(text.lower().split())
            all_words.update(words)

        return [{"keyword": w, "count": c} for w, c in all_words.most_common(top_n)]

    def add_domain(self, name: str, weights: Dict[str, float]):
        """Add or update domain keyword weights."""
        self._domain_weights[name] = weights
