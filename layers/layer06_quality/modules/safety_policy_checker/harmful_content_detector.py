"""Harmful Content Detector — Detect hate speech, violence, adult content.

Uses rule-based pattern matching with confidence scoring.
Categories: hate, violence, adult, self_harm, harassment, discrimination.
"""
from __future__ import annotations
import re
from typing import Dict, List

from layers.layer06_quality.modules.safety_policy_checker.safety_report import SafetyFlag


CATEGORY_PATTERNS: Dict[str, Dict[str, List[re.Pattern]]] = {
    "hate": {
        "slurs": [re.compile(r'\b(?:slur_words)\b', re.IGNORECASE)],
        "dehumanization": [
            re.compile(r'\b(?:animals?|vermin|parasites?|cockroaches?|rats?)\s+(?:deserve|need)\s+(?:to\s+)?(?:die|be\s+(?:killed|eliminated))', re.IGNORECASE),
        ],
        "supremacy": [
            re.compile(r'\b(?:supremacy|superior\s+race|master\s+race)\b', re.IGNORECASE),
        ],
    },
    "violence": {
        "threats": [
            re.compile(r'\b(?:kill|murder|destroy|attack)\s+(?:you|him|her|them|everyone)\b', re.IGNORECASE),
            re.compile(r'\b(?:i\'ll|i\s+will)\s+(?:kill|murder|destroy|beat)\b', re.IGNORECASE),
        ],
        "glorification": [
            re.compile(r'\b(?:glorif|prais|celebrat)\w*\s+(?:violence|murder|killing|attack)\b', re.IGNORECASE),
        ],
        "weapons": [
            re.compile(r'\b(?:how\s+to\s+(?:make|build|use)\s+(?:a\s+)?(?:bomb|explosive|weapon))\b', re.IGNORECASE),
        ],
    },
    "adult": {
        "explicit": [
            re.compile(r'\b(?:pornograph|explicit\s+sexual|sexually\s+explicit)\b', re.IGNORECASE),
        ],
        "exploitation": [
            re.compile(r'\b(?:exploitat)\w*\s+(?:of\s+)?(?:children|minors|underage)\b', re.IGNORECASE),
        ],
    },
    "self_harm": {
        "encouragement": [
            re.compile(r'\b(?:how\s+to\s+(?:commit|attempt)\s+suicide)\b', re.IGNORECASE),
            re.compile(r'\b(?:encourag|promot|glorif)\w*\s+(?:self[\s-]harm|suicide|cutting)\b', re.IGNORECASE),
        ],
    },
    "harassment": {
        "targeted": [
            re.compile(r'\b(?:you\s+(?:are|\'re)\s+(?:stupid|ugly|worthless|trash|garbage))\b', re.IGNORECASE),
            re.compile(r'\b(?:go\s+(?:die|kill)\s+yourself)\b', re.IGNORECASE),
        ],
    },
    "discrimination": {
        "protected_groups": [
            re.compile(r'\b(?:all|every|those)\s+(?:\w+\s+)?(?:people|men|women|immigrants|refugees)\s+(?:are|should)\s+(?:be\s+)?(?:banned|removed|killed|deported)\b', re.IGNORECASE),
        ],
    },
}

SEVERITY_WEIGHTS = {
    "critical": 0.3,
    "high": 0.15,
    "medium": 0.05,
    "low": 0.01,
}


class HarmfulContentDetector:
    """Detect harmful content using rule-based pattern matching."""

    def __init__(self, sensitivity: float = 0.5) -> None:
        self._sensitivity = max(0.0, min(1.0, sensitivity))
        self._check_count = 0

    def detect(self, text: str) -> List[SafetyFlag]:
        """Detect all harmful content categories in text."""
        flags: List[SafetyFlag] = []
        text_lower = text.lower()

        for category, subcategories in CATEGORY_PATTERNS.items():
            for subcat_name, patterns in subcategories.items():
                for pattern in patterns:
                    matches = pattern.finditer(text)
                    for match in matches:
                        confidence = self._calculate_confidence(
                            text_lower, match.group(), category
                        )
                        if confidence >= self._sensitivity * 0.3:
                            flag = SafetyFlag(
                                category=category,
                                subcategory=subcat_name,
                                severity=self._classify_severity(confidence),
                                confidence=confidence,
                                matched_text=match.group(),
                                description=f"Detected {category} content ({subcat_name})",
                                suggestion=f"Review and potentially remove {category} content",
                            )
                            flags.append(flag)

        self._check_count += 1
        return flags

    def detect_category(self, text: str, category: str) -> List[SafetyFlag]:
        """Detect a specific harmful category."""
        all_flags = self.detect(text)
        return [f for f in all_flags if f.category == category]

    def has_critical_issues(self, flags: List[SafetyFlag]) -> bool:
        """Check if any flags are critical severity."""
        return any(f.severity == "critical" for f in flags)

    def _calculate_confidence(self, text: str, match: str, category: str) -> float:
        """Calculate confidence based on context."""
        base = 0.6
        # Boost if repeated harmful content
        match_count = text.count(match.lower())
        if match_count > 1:
            base += 0.15
        # Boost for direct threats (second person)
        if re.search(r'\byou\b', match, re.IGNORECASE):
            base += 0.1
        # Category-specific base confidence
        category_boost = {"hate": 0.1, "violence": 0.1, "adult": 0.15,
                          "self_harm": 0.2, "harassment": 0.05}
        base += category_boost.get(category, 0)
        return min(1.0, base)

    def _classify_severity(self, confidence: float) -> str:
        """Classify severity from confidence."""
        if confidence >= 0.75:
            return "critical"
        if confidence >= 0.65:
            return "high"
        if confidence >= 0.4:
            return "medium"
        return "low"

    @property
    def check_count(self) -> int:
        return self._check_count
