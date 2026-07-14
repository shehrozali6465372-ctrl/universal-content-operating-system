"""Hypothesis Engine - Generates and tests hypotheses about trends."""
from __future__ import annotations
import time
from typing import Dict, List, Optional


class Hypothesis:
    """A testable hypothesis."""
    __slots__ = ("statement", "confidence", "evidence_for", "evidence_against",
                 "status", "created_at")

    def __init__(self, statement: str = "", confidence: float = 0.5):
        self.statement = statement
        self.confidence = confidence
        self.evidence_for: List[str] = []
        self.evidence_against: List[str] = []
        self.status = "proposed"  # proposed, supported, refuted, inconclusive
        self.created_at = time.time()

    def to_dict(self) -> Dict:
        return {
            "statement": self.statement, "confidence": round(self.confidence, 3),
            "evidence_for": list(self.evidence_for),
            "evidence_against": list(self.evidence_against),
            "status": self.status,
        }


class HypothesisResult:
    """Result of hypothesis testing."""
    __slots__ = ("hypothesis", "test_results", "verdict", "confidence_adjustment")

    def __init__(self) -> None:
        self.hypothesis: Optional[Hypothesis] = None
        self.test_results: List[Dict] = []
        self.verdict = "inconclusive"
        self.confidence_adjustment = 0.0

    def to_dict(self) -> Dict:
        return {
            "hypothesis": self.hypothesis.to_dict() if self.hypothesis else None,
            "test_results": list(self.test_results),
            "verdict": self.verdict,
            "confidence_adjustment": round(self.confidence_adjustment, 3),
        }


class HypothesisEngine:
    """Generates and tests hypotheses."""

    def __init__(self) -> None:
        self._hypotheses: List[Hypothesis] = []

    def propose(self, statement: str, confidence: float = 0.5) -> Hypothesis:
        h = Hypothesis(statement, confidence)
        self._hypotheses.append(h)
        return h

    def add_evidence_for(self, hypothesis: Hypothesis, evidence: str) -> None:
        hypothesis.evidence_for.append(evidence)
        hypothesis.confidence = min(1.0, hypothesis.confidence + 0.1)

    def add_evidence_against(self, hypothesis: Hypothesis, evidence: str) -> None:
        hypothesis.evidence_against.append(evidence)
        hypothesis.confidence = max(0.0, hypothesis.confidence - 0.1)

    def evaluate(self, hypothesis: Hypothesis) -> HypothesisResult:
        result = HypothesisResult()
        result.hypothesis = hypothesis

        pos = len(hypothesis.evidence_for)
        neg = len(hypothesis.evidence_against)
        total = pos + neg

        if total == 0:
            result.verdict = "inconclusive"
            hypothesis.status = "inconclusive"
        elif pos > neg * 2:
            result.verdict = "supported"
            hypothesis.status = "supported"
            result.confidence_adjustment = 0.2
        elif neg > pos * 2:
            result.verdict = "refuted"
            hypothesis.status = "refuted"
            result.confidence_adjustment = -0.3
        else:
            result.verdict = "inconclusive"
            hypothesis.status = "inconclusive"

        result.test_results.append({"verdict": result.verdict, "pos": pos, "neg": neg})
        return result

    def get_supported(self) -> List[Hypothesis]:
        return [h for h in self._hypotheses if h.status == "supported"]

    def get_refuted(self) -> List[Hypothesis]:
        return [h for h in self._hypotheses if h.status == "refuted"]

    def count(self) -> int:
        return len(self._hypotheses)
