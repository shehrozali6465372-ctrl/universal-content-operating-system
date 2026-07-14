"""
Batch Processor — Sprint 4 (v4.0)

Batch analysis with shared embedding cache and performance metrics.

Public API:
    analyze_many(texts, domain) -> List[SemanticResult]
    analyze_with_cache(text, domain) -> SemanticResult
    get_metrics() -> Dict
    clear_cache()

Version: 4.0.0
"""

from __future__ import annotations
import time
from typing import Dict, List


class BatchMetrics:
    """Performance metrics for batch processing."""

    __slots__ = ("total_analyses", "total_time_ms", "cache_hits", "cache_misses",
                 "avg_time_ms", "texts_per_second")

    def __init__(self) -> None:
        self.total_analyses: int = 0
        self.total_time_ms: float = 0.0
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        self.avg_time_ms: float = 0.0
        self.texts_per_second: float = 0.0

    def record(self, time_ms: float, cached: bool = False) -> None:
        self.total_analyses += 1
        self.total_time_ms += time_ms
        if cached:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        self.avg_time_ms = self.total_time_ms / max(self.total_analyses, 1)
        self.texts_per_second = 1000.0 / max(self.avg_time_ms, 0.001)

    def to_dict(self) -> Dict:
        return {
            "total_analyses": self.total_analyses,
            "total_time_ms": round(self.total_time_ms, 2),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(self.cache_hits / max(self.cache_hits + self.cache_misses, 1), 3),
            "avg_time_ms": round(self.avg_time_ms, 2),
            "texts_per_second": round(self.texts_per_second, 1),
        }


class BatchProcessor:
    """Batch semantic analysis with caching.

    Usage::

        from layers.layer03_intelligence.modules.content_understanding.semantic_analyzer import SemanticAnalyzer

        processor = BatchProcessor(SemanticAnalyzer())
        results = processor.analyze_many(["text1", "text2", "text3"])
        print(processor.get_metrics())
    """

    def __init__(self, analyzer=None) -> None:
        if analyzer is None:
            from layers.layer03_intelligence.modules.content_understanding.semantic_analyzer import SemanticAnalyzer
            analyzer = SemanticAnalyzer()
        self._analyzer = analyzer
        self._cache: Dict[str, object] = {}
        self._metrics = BatchMetrics()

    def analyze_many(self, texts: List[str], domain: str = "general") -> list:
        """Analyze multiple texts in batch.

        Uses shared cache to avoid re-analyzing identical texts.
        Returns list of SemanticResult objects.
        """
        results = []
        for text in texts:
            r = self.analyze_with_cache(text, domain)
            results.append(r)
        return results

    def analyze_with_cache(self, text: str, domain: str = "general") -> object:
        """Analyze a single text with cache check."""
        cache_key = f"{text.strip().lower()}:{domain}"

        # Check cache
        cached = self._cache.get(cache_key)
        if cached is not None:
            self._metrics.record(0.0, cached=True)
            return cached

        # Analyze
        start = time.time()
        result = self._analyzer.analyze(text)
        elapsed_ms = (time.time() - start) * 1000

        # Store in cache
        self._cache[cache_key] = result
        self._metrics.record(elapsed_ms, cached=False)

        return result

    def get_metrics(self) -> Dict:
        return self._metrics.to_dict()

    def cache_size(self) -> int:
        return len(self._cache)

    def clear_cache(self) -> None:
        self._cache.clear()

    def reset_metrics(self) -> None:
        self._metrics = BatchMetrics()
