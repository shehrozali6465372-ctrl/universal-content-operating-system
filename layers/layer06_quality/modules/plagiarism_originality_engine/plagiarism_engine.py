"""Plagiarism Engine — Core orchestrator for plagiarism and originality checking.

Orchestrates:
- Phrase detection (exact repeats, clichés, n-grams)
- Originality scoring (vocabulary, structure, ideas)
- Self-plagiarism checking
- Rewrite suggestions
"""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer06_quality.modules.plagiarism_originality_engine.phrase_detector import PhraseDetector
from layers.layer06_quality.modules.plagiarism_originality_engine.originality_scorer import OriginalityScorer
from layers.layer06_quality.modules.plagiarism_originality_engine.self_plagiarism_checker import SelfPlagiarismChecker
from layers.layer06_quality.modules.plagiarism_originality_engine.rewrite_suggester import RewriteSuggester
from layers.layer06_quality.modules.plagiarism_originality_engine.originality_report import OriginalityReport


class PlagiarismEngine:
    """Orchestrates full plagiarism and originality pipeline."""

    def __init__(
        self,
        phrase_detector: Optional[PhraseDetector] = None,
        originality_scorer: Optional[OriginalityScorer] = None,
        self_plagiarism_checker: Optional[SelfPlagiarismChecker] = None,
        rewrite_suggester: Optional[RewriteSuggester] = None,
    ) -> None:
        self.phrase_detector = phrase_detector or PhraseDetector()
        self.originality_scorer = originality_scorer or OriginalityScorer()
        self.self_plagiarism_checker = self_plagiarism_checker or SelfPlagiarismChecker()
        self.rewrite_suggester = rewrite_suggester or RewriteSuggester()
        self._check_count = 0

    def check(self, content: str) -> OriginalityReport:
        """Full originality check pipeline."""
        report = OriginalityReport()
        start_time = time.time()

        # Step 1: Exact phrase repeats
        repeats = self.phrase_detector.detect_exact_repeats(content)
        for seg in repeats:
            report.flagged_segments.append(seg)

        # Step 2: Clichés
        cliches = self.phrase_detector.detect_cliches(content)
        for seg in cliches:
            report.flagged_segments.append(seg)

        # Step 3: N-gram duplicates
        ngram_dups = self.phrase_detector.detect_ngram_duplicates(content)
        for seg in ngram_dups:
            report.flagged_segments.append(seg)

        # Step 4: Originality scoring
        signals = self.originality_scorer.score(content)
        overall_score = self.originality_scorer.get_overall_score(signals)

        # Step 5: Self-plagiarism
        self_matches = self.self_plagiarism_checker.check(content)
        report.self_plagiarism_matches = self_matches

        # Step 6: Rewrite suggestions
        suggestions = self.rewrite_suggester.suggest_for_segments(report.flagged_segments)
        report.statistics["rewrite_suggestions"] = [s.to_dict() for s in suggestions]

        # Step 7: Compute overall
        report.compute_overall()

        # Blend originality scorer with flag-based score
        report.overall_originality_score = round(
            (report.overall_originality_score * 0.5 + overall_score * 0.5), 3
        )
        report.is_original = report.overall_originality_score >= 0.7

        # Update statistics
        elapsed = time.time() - start_time
        report.statistics["check_time_ms"] = round(elapsed * 1000, 2)
        report.statistics["content_length"] = len(content)
        report.statistics["originality_signals"] = signals
        report.statistics["originality_score_computed"] = overall_score

        self._check_count += 1
        return report

    def check_quick(self, content: str) -> Dict[str, Any]:
        """Quick check returning summary dict."""
        report = self.check(content)
        return {
            "is_original": report.is_original,
            "originality_score": report.overall_originality_score,
            "flagged_segments": len(report.flagged_segments),
            "self_plagiarism_matches": len(report.self_plagiarism_matches),
            "rewrite_suggestions": report.statistics.get("rewrite_suggestions", []),
        }

    def check_batch(self, contents: List[str]) -> List[OriginalityReport]:
        """Check multiple content pieces."""
        return [self.check(c) for c in contents]

    @property
    def check_count(self) -> int:
        return self._check_count
