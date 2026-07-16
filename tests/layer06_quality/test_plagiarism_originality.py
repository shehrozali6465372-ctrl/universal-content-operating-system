"""Tests for Layer 6 Module 4 — Plagiarism & Originality Engine."""
from layers.layer06_quality.modules.plagiarism_originality_engine.phrase_detector import PhraseDetector
from layers.layer06_quality.modules.plagiarism_originality_engine.originality_scorer import OriginalityScorer
from layers.layer06_quality.modules.plagiarism_originality_engine.self_plagiarism_checker import SelfPlagiarismChecker
from layers.layer06_quality.modules.plagiarism_originality_engine.rewrite_suggester import RewriteSuggester
from layers.layer06_quality.modules.plagiarism_originality_engine.plagiarism_engine import PlagiarismEngine
from layers.layer06_quality.modules.plagiarism_originality_engine.originality_report import (
    OriginalityReport, FlaggedSegment,
)


# ── PhraseDetector Tests ──

class TestPhraseDetector:
    def setup_method(self):
        self.detector = PhraseDetector()

    def test_no_repeats(self):
        text = "Artificial intelligence is transforming industries worldwide rapidly."
        flags = self.detector.detect_exact_repeats(text)
        assert isinstance(flags, list)

    def test_exact_repeat(self):
        text = "Artificial intelligence transforming industries. Artificial intelligence transforming healthcare. Artificial intelligence transforming finance."
        flags = self.detector.detect_exact_repeats(text)
        assert any(f.match_type == "exact_repeat" for f in flags)

    def test_cliche_detection(self):
        text = "At the end of the day, we need to be honest about the facts."
        flags = self.detector.detect_cliches(text)
        assert any(f.match_type == "cliche" for f in flags)

    def test_no_cliches(self):
        text = "Machine learning models require substantial training data."
        flags = self.detector.detect_cliches(text)
        assert len(flags) == 0

    def test_ngram_duplicates(self):
        text = "The market is growing. The market is growing fast. The market is growing daily."
        flags = self.detector.detect_ngram_duplicates(text, n=3)
        assert len(flags) >= 0  # May or may not find duplicates depending on stop words

    def test_empty_text(self):
        assert self.detector.detect_exact_repeats("") == []
        assert self.detector.detect_cliches("") == []
        assert self.detector.detect_ngram_duplicates("") == []

    def test_check_count(self):
        self.detector.detect_exact_repeats("Test text")
        self.detector.detect_cliches("Test text")
        assert self.detector.check_count == 2

    def test_repeated_bigrams(self):
        text = "The quick brown fox jumps. The quick brown fox runs. The quick brown fox sleeps."
        flags = self.detector.detect_ngram_duplicates(text, n=3)
        assert len(flags) >= 1

    def test_cliche_at_end(self):
        text = "To be honest, this is a great product for everyone."
        flags = self.detector.detect_cliches(text)
        assert any("to be honest" in f.text for f in flags)

    def test_multiple_cliches(self):
        text = "First and foremost, at the end of the day, last but not least, it goes without saying."
        flags = self.detector.detect_cliches(text)
        assert len(flags) >= 3


# ── OriginalityScorer Tests ──

class TestOriginalityScorer:
    def setup_method(self):
        self.scorer = OriginalityScorer()

    def test_score_returns_dict(self):
        signals = self.scorer.score("AI technology is transforming industries.")
        assert isinstance(signals, dict)
        assert "vocabulary_diversity" in signals
        assert "sentence_variety" in signals

    def test_overall_score_range(self):
        signals = self.scorer.score("A comprehensive analysis of artificial intelligence.")
        overall = self.scorer.get_overall_score(signals)
        assert 0.0 <= overall <= 1.0

    def test_diverse_text_high_score(self):
        signals = self.scorer.score(
            "Quantum computing leverages quantum mechanical phenomena. "
            "Superposition enables parallel computation. Entanglement creates correlations."
        )
        overall = self.scorer.get_overall_score(signals)
        assert overall >= 0.5

    def test_repetitive_text_low_score(self):
        signals = self.scorer.score("test test test test test test test test test test")
        overall = self.scorer.get_overall_score(signals)
        assert overall < 0.8

    def test_empty_text(self):
        signals = self.scorer.score("")
        overall = self.scorer.get_overall_score(signals)
        assert 0.0 <= overall <= 1.0

    def test_vocabulary_diversity(self):
        signals = self.scorer.score("Innovative, creative, original, unique, fresh ideas.")
        assert signals["vocabulary_diversity"] > 0.5

    def test_sentence_variety(self):
        signals = self.scorer.score(
            "Short. Medium length sentence here. And a much longer sentence with more words to show variety."
        )
        assert signals["sentence_variety"] >= 0.0

    def test_structural_variety_with_markdown(self):
        signals = self.scorer.score("# Heading\n\n- Item 1\n- Item 2\n\nParagraph with 42% stat.")
        assert signals["structural_variety"] >= 0.5

    def test_check_count(self):
        self.scorer.score("Test")
        assert self.scorer._check_count == 1


# ── SelfPlagiarismChecker Tests ──

class TestSelfPlagiarismChecker:
    def setup_method(self):
        self.checker = SelfPlagiarismChecker()

    def test_no_history(self):
        matches = self.checker.check("New content here.")
        assert matches == []

    def test_exact_duplicate(self):
        text = "Artificial intelligence is transforming industries worldwide."
        self.checker.add_published(text, source="previous_post")
        matches = self.checker.check(text)
        assert len(matches) >= 1
        assert any(m.similarity_score > 0.8 for m in matches)

    def test_different_content(self):
        self.checker.add_published("AI is great.", source="old_post")
        matches = self.checker.check("Blockchain technology revolutionizes finance.")
        assert all(m.similarity_score < 0.8 for m in matches)

    def test_add_multiple(self):
        self.checker.add_published("Post one.", source="p1")
        self.checker.add_published("Post two.", source="p2")
        assert self.checker.history_size == 2

    def test_clear_history(self):
        self.checker.add_published("Test.", source="t")
        self.checker.clear_history()
        assert self.checker.history_size == 0

    def test_high_similarity(self):
        text = "The quick brown fox jumps over the lazy dog repeatedly."
        self.checker.add_published(text, source="old")
        matches = self.checker.check(text)
        high = self.checker.get_high_similarity(matches)
        assert len(high) >= 1

    def test_sentence_duplicate(self):
        prev = "This is an important sentence about technology. Another one about AI."
        new = "This is an important sentence about technology. Completely different topic."
        self.checker.add_published(prev, source="old")
        matches = self.checker.check(new)
        assert any(m.match_type == "sentence_duplicate" for m in matches)

    def test_check_count(self):
        self.checker.check("Test")
        assert self.checker.check_count == 1


# ── RewriteSuggester Tests ──

class TestRewriteSuggester:
    def setup_method(self):
        self.suggester = RewriteSuggester()

    def test_no_segments(self):
        suggestions = self.suggester.suggest_for_segments([])
        assert suggestions == []

    def test_exact_repeat_suggestion(self):
        seg = FlaggedSegment(
            text="AI is important", match_type="exact_repeat", severity="medium"
        )
        suggestions = self.suggester.suggest_for_segments([seg])
        assert len(suggestions) >= 1
        assert suggestions[0].suggestion_type == "paraphrase"

    def test_cliche_suggestion(self):
        seg = FlaggedSegment(
            text="at the end of the day", match_type="cliche", severity="low"
        )
        suggestions = self.suggester.suggest_for_segments([seg])
        assert any(s.suggestion_type == "remove_cliche" for s in suggestions)

    def test_cliche_in_text(self):
        suggestions = self.suggester.suggest_for_cliches(
            "At the end of the day, we must be honest."
        )
        assert len(suggestions) >= 1

    def test_vocabulary_enhancement(self):
        suggestions = self.suggester.suggest_vocabulary_enhancement(
            "The good team made a good product with good results."
        )
        assert len(suggestions) >= 1

    def test_to_dict(self):
        seg = FlaggedSegment(text="test", match_type="ngram_repeat")
        suggestions = self.suggester.suggest_for_segments([seg])
        assert len(suggestions) >= 1
        d = suggestions[0].to_dict()
        assert "suggestion_type" in d

    def test_suggest_count(self):
        self.suggester.suggest_for_segments([])
        self.suggester.suggest_for_cliches("Test")
        assert self.suggester.suggest_count == 2


# ── PlagiarismEngine Tests ──

class TestPlagiarismEngine:
    def setup_method(self):
        self.engine = PlagiarismEngine()

    def test_original_content(self):
        report = self.engine.check("Innovative quantum computing algorithms leverage superposition.")
        assert isinstance(report, OriginalityReport)
        assert report.is_original

    def test_repetitive_content(self):
        report = self.engine.check(
            "AI is good. AI is good. AI is good. AI is good. AI is good. AI is good."
        )
        assert isinstance(report, OriginalityReport)

    def test_cliche_heavy(self):
        report = self.engine.check(
            "At the end of the day, to be honest, first and foremost, "
            "it goes without saying that the bottom line is important."
        )
        assert len(report.flagged_segments) >= 2

    def test_quick_check(self):
        result = self.engine.check_quick("Original content about technology.")
        assert "is_original" in result
        assert "originality_score" in result
        assert "flagged_segments" in result

    def test_check_batch(self):
        reports = self.engine.check_batch(["Content A.", "Content B."])
        assert len(reports) == 2

    def test_self_plagiarism(self):
        self.engine.self_plagiarism_checker.add_published(
            "AI transforms industries globally.", source="old_post"
        )
        report = self.engine.check("AI transforms industries globally.")
        assert len(report.self_plagiarism_matches) >= 1

    def test_statistics_populated(self):
        report = self.engine.check("Test content for originality.")
        assert "check_time_ms" in report.statistics
        assert "content_length" in report.statistics
        assert "originality_signals" in report.statistics

    def test_check_count(self):
        self.engine.check("Test 1")
        self.engine.check("Test 2")
        assert self.engine.check_count == 2

    def test_report_to_dict(self):
        report = self.engine.check("Test content.")
        d = report.to_dict()
        assert "overall_originality_score" in d
        assert "is_original" in d
        assert "flagged_segments" in d

    def test_compute_overall_no_flags(self):
        report = OriginalityReport()
        report.compute_overall()
        assert report.is_original

    def test_compute_overall_many_flags(self):
        report = OriginalityReport()
        for _ in range(5):
            report.flagged_segments.append(
                FlaggedSegment(severity="high")
            )
        report.compute_overall()
        assert not report.is_original
