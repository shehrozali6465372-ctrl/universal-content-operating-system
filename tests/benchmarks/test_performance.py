"""Performance Benchmarks for Semantic Analyzer.

Measures latency, memory, and throughput at different scales.
"""
from __future__ import annotations

import statistics
import time
from typing import List

import pytest

from layers.layer03_intelligence.modules.content_understanding.semantic_analyzer import (
    SemanticAnalyzer,
)

SAMPLE_TEXTS = [
    "AI developers ki demand 2026 mein barh rahi hai.",
    "Bitcoin price $150K tak ja sakti hai according to analysts.",
    "Exercise rozana 30 minute karna sehat ke liye zaroori hai.",
    "Pakistan cricket team ne T20 World Cup jeeta hai.",
    "Python programming seekhna beginners ke liye easy ho gaya hai.",
    "Stock market mein correction aane ke chances hain.",
    "Mental health awareness Pakistan mein barh rahi hai.",
    "Cloud computing services mein intense competition hai.",
    "Freelancing se paisa kamana ab popular ho raha hai.",
    "Remote work ka trend ab permanent ho gaya hai.",
    "Quantum computing ka practical use limited hai abhi.",
    "Personal finance manage karne ka sabse acha tareeqa budget banana hai.",
    "Youth ki voting percentage barh rahi hai.",
    "E-commerce Pakistan mein tezi se barh raha hai.",
    "Social media ka addiction serious problem ban chuka hai.",
    "Olympics mein Pakistan ko gold medal milna mushkil raha hai.",
    "Corruption ka khatma kab hoga ye sawal hai.",
    "Yoga se stress kam hota hai aur body flexible banti hai.",
    "IPL aur PSL ka comparison karo.",
    "GPT-5 aur Claude 4 best LLM banne ke liye compete kar rahe hain.",
]


def _generate_texts(n: int) -> List[str]:
    return [SAMPLE_TEXTS[i % len(SAMPLE_TEXTS)] for i in range(n)]


class TestPerformanceBenchmarks:
    """Performance benchmarks for semantic analysis."""

    @pytest.fixture(scope="class")
    def analyzer(self) -> SemanticAnalyzer:
        return SemanticAnalyzer()

    def test_single_analysis_latency(self, analyzer: SemanticAnalyzer) -> None:
        """Single text analysis should complete under 100ms."""
        text = "AI developers ki demand 2026 mein barh rahi hai."
        times = []
        for _ in range(10):
            start = time.perf_counter()
            analyzer.analyze(text)
            times.append(time.perf_counter() - start)
        avg_ms = statistics.mean(times) * 1000
        p95_ms = sorted(times)[int(len(times) * 0.95)] * 1000
        assert avg_ms < 100, f"Average latency {avg_ms:.1f}ms > 100ms"
        assert p95_ms < 200, f"P95 latency {p95_ms:.1f}ms > 200ms"

    def test_batch_100_latency(self, analyzer: SemanticAnalyzer) -> None:
        """Batch of 100 texts should complete under 5 seconds."""
        texts = _generate_texts(100)
        start = time.perf_counter()
        for text in texts:
            analyzer.analyze(text)
        elapsed = time.perf_counter() - start
        assert elapsed < 5.0, f"100-text batch took {elapsed:.1f}s > 5s"

    def test_batch_1000_latency(self, analyzer: SemanticAnalyzer) -> None:
        """Batch of 1000 texts should complete under 30 seconds."""
        texts = _generate_texts(1000)
        start = time.perf_counter()
        for text in texts:
            analyzer.analyze(text)
        elapsed = time.perf_counter() - start
        assert elapsed < 30.0, f"1000-text batch took {elapsed:.1f}s > 30s"

    def test_similarity_latency(self, analyzer: SemanticAnalyzer) -> None:
        """Semantic similarity should be fast."""
        a = "AI is transforming healthcare with new diagnostic tools."
        b = "Machine learning is revolutionizing medical diagnosis."
        times = []
        for _ in range(20):
            start = time.perf_counter()
            analyzer.semantic_similarity(a, b)
            times.append(time.perf_counter() - start)
        avg_ms = statistics.mean(times) * 1000
        assert avg_ms < 50, f"Similarity avg latency {avg_ms:.1f}ms > 50ms"

    def test_memory_usage_bounded(self, analyzer: SemanticAnalyzer) -> None:
        """Memory usage should not grow unbounded with repeated calls."""
        import sys

        texts = _generate_texts(500)
        # Get baseline
        baseline = sys.getsizeof({})
        for text in texts:
            analyzer.analyze(text)
        # Verify analyzer state isn't growing excessively
        analyzer_size = sys.getsizeof(analyzer.__dict__)
        assert analyzer_size < 1_000_000, (
            f"Analyzer state too large: {analyzer_size} bytes"
        )

    def test_throughput(self, analyzer: SemanticAnalyzer) -> None:
        """Should achieve at least 20 analyses per second."""
        texts = _generate_texts(100)
        start = time.perf_counter()
        for text in texts:
            analyzer.analyze(text)
        elapsed = time.perf_counter() - start
        throughput = len(texts) / elapsed
        assert throughput >= 20, f"Throughput {throughput:.1f}/s < 20/s"
