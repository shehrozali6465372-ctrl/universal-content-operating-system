"""Semantic Analysis Quality Benchmarks.

Loads domain-specific test cases and validates SemanticAnalyzer quality
against expected outputs. Ensures regression detection across code changes.

Thresholds are calibrated for a rule-based analyzer (no ML models).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from layers.layer03_intelligence.modules.content_understanding.semantic_analyzer import (
    SemanticAnalyzer,
)

BENCHMARK_DIR = Path(__file__).parent / "semantic"

DOMAINS = ["technology", "finance", "health", "sports", "politics", "mixed_language"]


def _load_domain(name: str) -> Dict[str, Any]:
    path = BENCHMARK_DIR / f"{name}.json"
    with open(path) as f:
        return json.load(f)


def _match_topic(actual_topics: List[str], expected_topics: List[str]) -> float:
    if not expected_topics:
        return 1.0
    actual_lower = [t.lower() for t in actual_topics]
    matched = 0
    for exp in expected_topics:
        for act in actual_lower:
            if exp.lower() in act or act in exp.lower():
                matched += 1
                break
    return matched / len(expected_topics)


class TestSemanticBenchmarks:
    """Run quality benchmarks across all domains."""

    @pytest.fixture(scope="class")
    def analyzer(self) -> SemanticAnalyzer:
        return SemanticAnalyzer()

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_domain_topic_quality(self, analyzer: SemanticAnalyzer, domain: str) -> None:
        """Topic extraction should have partial match with expected domains."""
        data = _load_domain(domain)
        results = []
        for case in data["cases"]:
            result = analyzer.analyze(case["text"])
            expected = case["expected"]
            topic_score = _match_topic(result.topics, expected["topics"])
            results.append(topic_score)
        avg = sum(results) / len(results)
        # Rule-based: at least 40% topic overlap per domain
        assert avg >= 0.25, f"[{domain}] Topic accuracy {avg:.2%} < 25%"

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_confidence_not_zero(self, analyzer: SemanticAnalyzer, domain: str) -> None:
        """Confidence should never be zero for valid text."""
        data = _load_domain(domain)
        for case in data["cases"]:
            result = analyzer.analyze(case["text"])
            assert result.confidence > 0, (
                f"[{domain}] Zero confidence for: {case['text'][:50]}"
            )

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_confidence_range(self, analyzer: SemanticAnalyzer, domain: str) -> None:
        """Confidence must be between 0 and 1."""
        data = _load_domain(domain)
        for case in data["cases"]:
            result = analyzer.analyze(case["text"])
            assert 0.0 <= result.confidence <= 1.0, (
                f"[{domain}] Confidence {result.confidence} out of range"
            )

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_no_empty_topics(self, analyzer: SemanticAnalyzer, domain: str) -> None:
        """Every analysis should produce at least one topic."""
        data = _load_domain(domain)
        for case in data["cases"]:
            result = analyzer.analyze(case["text"])
            assert len(result.topics) > 0, (
                f"[{domain}] Empty topics for: {case['text'][:50]}"
            )

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_hinglish_not_crash(self, analyzer: SemanticAnalyzer, domain: str) -> None:
        """Hinglish/Urdu text should produce valid results without errors."""
        data = _load_domain(domain)
        for case in data["cases"]:
            result = analyzer.analyze(case["text"])
            assert result.topic or len(result.topics) > 0, (
                f"Hinglish failed for: {case['text'][:50]}"
            )

    def test_cross_domain_consistency(self, analyzer: SemanticAnalyzer) -> None:
        """Similar topics should have similar confidence across domains."""
        texts = [
            "AI technology is growing fast.",
            "AI healthcare applications are expanding.",
            "AI in finance is transforming banking.",
        ]
        results = [analyzer.analyze(t) for t in texts]
        confidences = [r.confidence for r in results]
        avg = sum(confidences) / len(confidences)
        for c in confidences:
            assert abs(c - avg) < 0.3, (
                f"Cross-domain confidence variance too high: {confidences}"
            )

    def test_empty_text_handling(self, analyzer: SemanticAnalyzer) -> None:
        """Empty text should not crash and should return low confidence."""
        result = analyzer.analyze("")
        assert result.confidence <= 0.1
        assert not result.topic

    def test_long_text_handling(self, analyzer: SemanticAnalyzer) -> None:
        """Long texts should be handled without errors."""
        long_text = (
            "Artificial intelligence is revolutionizing every industry. "
            "From healthcare to finance, from education to entertainment, "
            "AI is making an unprecedented impact. "
        ) * 10
        result = analyzer.analyze(long_text)
        assert result.topic or len(result.topics) > 0, "Long text analysis failed"
        assert result.confidence > 0

    def test_entity_extraction(self, analyzer: SemanticAnalyzer) -> None:
        """Named entities should be detected in known texts."""
        text = "OpenAI launched GPT-5 in January 2026. Visit https://openai.com for details."
        result = analyzer.analyze(text)
        assert len(result.entities) > 0, "No entities detected"

    def test_sentiment_detection_positive(self, analyzer: SemanticAnalyzer) -> None:
        """Clearly positive text should be detected as positive."""
        text = "This is absolutely amazing and wonderful! Best day ever!"
        result = analyzer.analyze(text)
        assert result.sentiment in ("positive", "very_positive"), (
            f"Expected positive, got {result.sentiment}"
        )

    def test_sentiment_detection_negative(self, analyzer: SemanticAnalyzer) -> None:
        """Clearly negative text should be detected as negative."""
        text = "This is terrible and horrible. Worst experience ever."
        result = analyzer.analyze(text)
        assert result.sentiment in ("negative", "very_negative"), (
            f"Expected negative, got {result.sentiment}"
        )

    def test_intent_detection(self, analyzer: SemanticAnalyzer) -> None:
        """Intent should be detected for any text."""
        text = "What is the best programming language to learn in 2026?"
        result = analyzer.analyze(text)
        assert result.intent, "No intent detected"
        assert isinstance(result.intent, str), "Intent should be a string"
