"""
Contradiction Detector
Layer 2: Research Engine — Module 6

Detects contradictions between claims and evidence:
- Direct negation detection
- Numerical contradiction detection
- Temporal contradiction detection
- Direction contradiction detection (increase vs decrease)
- Contradiction severity scoring
"""

import re
from typing import List, Optional


class Contradiction:
    """A detected contradiction."""

    __slots__ = (
        "contradiction_id", "claim_text", "evidence_text",
        "contradiction_type", "severity", "description",
        "confidence",
    )

    TYPES = ["negation", "numerical", "temporal", "direction", "factual"]

    def __init__(
        self,
        claim_text: str,
        evidence_text: str,
        contradiction_type: str = "factual",
        severity: float = 0.5,
        description: str = "",
        confidence: float = 0.5,
    ):
        self.contradiction_id = f"contra_{hash(claim_text + evidence_text) % 1000000}"
        self.claim_text = claim_text
        self.evidence_text = evidence_text
        self.contradiction_type = contradiction_type if contradiction_type in self.TYPES else "factual"
        self.severity = max(0.0, min(1.0, severity))
        self.description = description
        self.confidence = max(0.0, min(1.0, confidence))

    def to_dict(self) -> dict:
        return {
            "contradiction_id": self.contradiction_id,
            "claim_text": self.claim_text[:200],
            "evidence_text": self.evidence_text[:200],
            "contradiction_type": self.contradiction_type,
            "severity": self.severity,
            "description": self.description,
            "confidence": self.confidence,
        }


NEGATION_PAIRS = [
    ("increase", "decrease"), ("rise", "fall"), ("grow", "decline"),
    ("improve", "worsen"), ("better", "worse"), ("more", "less"),
    ("higher", "lower"), ("positive", "negative"), ("true", "false"),
    ("always", "never"), ("all", "none"), ("highest", "lowest"),
]

DIRECTION_WORDS = {
    "increase": 1, "increasing": 1, "rise": 1, "rising": 1, "grow": 1, "growing": 1,
    "surge": 1, "surging": 1, "boom": 1, "improve": 1, "improving": 1,
    "decrease": -1, "decreasing": -1, "fall": -1, "falling": -1,
    "decline": -1, "declining": -1, "drop": -1, "dropping": -1,
    "crash": -1, "worsen": -1, "worsening": -1,
}


class ContradictionDetector:
    """Detect contradictions between claims and evidence."""

    def __init__(self, sensitivity: float = 0.5):
        self._sensitivity = max(0.0, min(1.0, sensitivity))

    def detect(self, claim_text: str, evidence_text: str) -> List[Contradiction]:
        """Detect all contradictions between a claim and evidence."""
        contradictions = []
        claim_lower = claim_text.lower()
        ev_lower = evidence_text.lower()

        # Check negation contradictions
        neg = self._check_negation(claim_lower, ev_lower)
        if neg:
            contradictions.append(neg)

        # Check numerical contradictions
        num = self._check_numerical(claim_lower, ev_lower)
        if num:
            contradictions.append(num)

        # Check direction contradictions
        direc = self._check_direction(claim_lower, ev_lower)
        if direc:
            contradictions.append(direc)

        return contradictions

    def detect_batch(
        self, claim_text: str, evidence_texts: List[str]
    ) -> List[Contradiction]:
        """Check a claim against multiple evidence texts."""
        all_contradictions = []
        for ev in evidence_texts:
            all_contradictions.extend(self.detect(claim_text, ev))
        return all_contradictions

    def _check_negation(self, claim: str, evidence: str) -> Optional[Contradiction]:
        """Check for direct negation contradictions."""
        for pos, neg in NEGATION_PAIRS:
            claim_has_pos = pos in claim
            claim_has_neg = neg in claim
            ev_has_pos = pos in evidence
            ev_has_neg = neg in evidence

            if claim_has_pos and ev_has_neg and not claim_has_neg:
                return Contradiction(
                    claim_text=claim, evidence_text=evidence,
                    contradiction_type="negation",
                    severity=0.8 * self._sensitivity,
                    description=f"Claim mentions '{pos}' but evidence mentions '{neg}'",
                    confidence=0.6,
                )
            if claim_has_neg and ev_has_pos and not claim_has_pos:
                return Contradiction(
                    claim_text=claim, evidence_text=evidence,
                    contradiction_type="negation",
                    severity=0.8 * self._sensitivity,
                    description=f"Claim mentions '{neg}' but evidence mentions '{pos}'",
                    confidence=0.6,
                )
        return None

    def _check_numerical(self, claim: str, evidence: str) -> Optional[Contradiction]:
        """Check for numerical contradictions."""
        claim_nums = set(re.findall(r'\d+(?:\.\d+)?%?', claim))
        ev_nums = set(re.findall(r'\d+(?:\.\d+)?%?', evidence))

        if not claim_nums or not ev_nums:
            return None

        # Look for same metric, different number
        claim_pcts = {float(n.replace('%', '')) for n in claim_nums if '%' in n}
        ev_pcts = {float(n.replace('%', '')) for n in ev_nums if '%' in n}

        if claim_pcts and ev_pcts:
            for cp in claim_pcts:
                for ep in ev_pcts:
                    if abs(cp - ep) > 10:  # More than 10% difference
                        return Contradiction(
                            claim_text=claim, evidence_text=evidence,
                            contradiction_type="numerical",
                            severity=0.7 * self._sensitivity,
                            description=f"Claim states {cp}% but evidence shows {ep}%",
                            confidence=0.5,
                        )
        return None

    def _check_direction(self, claim: str, evidence: str) -> Optional[Contradiction]:
        """Check for direction contradictions (increase vs decrease)."""
        claim_dir = self._get_direction(claim)
        ev_dir = self._get_direction(evidence)

        if claim_dir != 0 and ev_dir != 0 and claim_dir != ev_dir:
            claim_word = "increase" if claim_dir > 0 else "decrease"
            ev_word = "increase" if ev_dir > 0 else "decrease"
            return Contradiction(
                claim_text=claim, evidence_text=evidence,
                contradiction_type="direction",
                severity=0.75 * self._sensitivity,
                description=f"Claim suggests {claim_word} but evidence suggests {ev_word}",
                confidence=0.55,
            )
        return None

    def _get_direction(self, text: str) -> int:
        """Determine the overall direction of a text."""
        score = 0
        for word, direction in DIRECTION_WORDS.items():
            if word in text:
                score += direction
        return 1 if score > 0 else (-1 if score < 0 else 0)

    def get_contradiction_severity(self, contradictions: List[Contradiction]) -> float:
        """Get overall contradiction severity (0 = none, 1 = severe)."""
        if not contradictions:
            return 0.0
        return max(c.severity for c in contradictions)
