"""Spam Detector — Detect spam, clickbait, and misleading content.

Checks:
- Clickbait patterns
- Excessive capitalization
- Spammy phrases
- Misleading claims
- Excessive punctuation
- Repetitive content
- Urgency manipulation
"""
from __future__ import annotations
import re
from typing import List

from layers.layer06_quality.modules.safety_policy_checker.safety_report import SafetyFlag


CLICKBAIT_PATTERNS = [
    re.compile(r'\byou\s+(?:won\'t|wont)\s+believe\b', re.IGNORECASE),
    re.compile(r'\bthis\s+(?:one\s+)?(?:trick|secret|hack)\b', re.IGNORECASE),
    re.compile(r'\bdoctors?\s+(?:hate|don\'t\s+want)\b', re.IGNORECASE),
    re.compile(r'\b(?:shocking|unbelievable|amazing)\s+(?:truth|secret|fact)\b', re.IGNORECASE),
    re.compile(r'\b(?:number\s+\d+|top\s+\d+)\s+(?:will\s+)?(?:shock|surprise|amaze)\b', re.IGNORECASE),
    re.compile(r'\bwhat\s+they\s+(?:don\'t|wont)\s+tell\s+you\b', re.IGNORECASE),
    re.compile(r'\b(?:get\s+rich|make\s+money|earn\s+\$)\s+(?:quick|fast|overnight|easy)\b', re.IGNORECASE),
]

SPAMMY_PHRASES = [
    re.compile(r'\b(?:buy\s+now|limited\s+time|act\s+now|hurry|don\'t\s+miss)\b', re.IGNORECASE),
    re.compile(r'\b(?:100%\s+free|no\s+cost|risk[\s-]free|guaranteed)\b', re.IGNORECASE),
    re.compile(r'\b(?:subscribe\s+now|follow\s+me|like\s+and\s+share)\b', re.IGNORECASE),
    re.compile(r'\b(?:dm\s+for|link\s+in\s+bio|check\s+(?:my|our)\s+(?:bio|profile))\b', re.IGNORECASE),
]

URGENCY_PATTERNS = [
    re.compile(r'\b(?:today\s+only|last\s+chance|ending\s+(?:soon|today))\b', re.IGNORECASE),
    re.compile(r'\b(?:don\'t\s+wait|before\s+it\'s\s+too\s+late|while\s+supplies?\s+last)\b', re.IGNORECASE),
]

MISLEADING_PATTERNS = [
    re.compile(r'\b(?:guaranteed|proven|clinically\s+(?:proven|tested))\b', re.IGNORECASE),
    re.compile(r'\b(?:make\s+\$?\d+k?\s+per\s+(?:day|week|month|hour))\b', re.IGNORECASE),
    re.compile(r'\b(?:lose\s+\d+\s+pounds?\s+in\s+\d+\s+days?)\b', re.IGNORECASE),
]


class SpamDetector:
    """Detect spam, clickbait, and misleading content."""

    def __init__(self, sensitivity: float = 0.5) -> None:
        self._sensitivity = max(0.0, min(1.0, sensitivity))
        self._check_count = 0

    def detect(self, text: str) -> List[SafetyFlag]:
        """Detect all spam-related issues."""
        flags: List[SafetyFlag] = []
        flags.extend(self._check_clickbait(text))
        flags.extend(self._check_spammy_phrases(text))
        flags.extend(self._check_excessive_caps(text))
        flags.extend(self._check_excessive_punctuation(text))
        flags.extend(self._check_repetition(text))
        flags.extend(self._check_urgency(text))
        flags.extend(self._check_misleading(text))
        self._check_count += 1
        return flags

    def _check_clickbait(self, text: str) -> List[SafetyFlag]:
        flags: List[SafetyFlag] = []
        for pattern in CLICKBAIT_PATTERNS:
            for match in pattern.finditer(text):
                conf = min(1.0, 0.7 + 0.1 * text.lower().count(match.group().lower()))
                if conf >= self._sensitivity * 0.5:
                    flags.append(SafetyFlag(
                        category="spam", subcategory="clickbait",
                        severity="medium", confidence=conf,
                        matched_text=match.group(),
                        description="Clickbait pattern detected",
                        suggestion="Rewrite to be more informative and less sensational",
                    ))
        return flags

    def _check_spammy_phrases(self, text: str) -> List[SafetyFlag]:
        flags: List[SafetyFlag] = []
        for pattern in SPAMMY_PHRASES:
            for match in pattern.finditer(text):
                conf = min(1.0, 0.65 + 0.1 * text.lower().count(match.group().lower()))
                if conf >= self._sensitivity * 0.5:
                    flags.append(SafetyFlag(
                        category="spam", subcategory="spammy_phrase",
                        severity="medium", confidence=conf,
                        matched_text=match.group(),
                        description="Spammy promotional phrase detected",
                        suggestion="Replace with genuine, value-driven language",
                    ))
        return flags

    def _check_excessive_caps(self, text: str) -> List[SafetyFlag]:
        flags: List[SafetyFlag] = []
        words = text.split()
        if len(words) < 3:
            return flags
        caps_words = [w for w in words if w.isupper() and len(w) > 1]
        ratio = len(caps_words) / len(words)
        if ratio > 0.4:
            severity = "high" if ratio > 0.7 else "medium" if ratio > 0.5 else "low"
            flags.append(SafetyFlag(
                category="spam", subcategory="excessive_caps",
                severity=severity, confidence=min(1.0, ratio),
                matched_text=f"{len(caps_words)} of {len(words)} words are ALL CAPS",
                description="Excessive capitalization detected",
                suggestion="Use normal capitalization for readability",
            ))
        return flags

    def _check_excessive_punctuation(self, text: str) -> List[SafetyFlag]:
        flags: List[SafetyFlag] = []
        exclaim = text.count("!")
        question = text.count("?")
        if exclaim > 3:
            flags.append(SafetyFlag(
                category="spam", subcategory="excessive_punctuation",
                severity="low", confidence=min(1.0, exclaim / 10),
                matched_text=f"{exclaim} exclamation marks",
                description="Excessive exclamation marks",
                suggestion="Reduce exclamation marks for professional tone",
            ))
        if question > 3:
            flags.append(SafetyFlag(
                category="spam", subcategory="excessive_punctuation",
                severity="low", confidence=min(1.0, question / 10),
                matched_text=f"{question} question marks",
                description="Excessive question marks",
                suggestion="Reduce question marks for professional tone",
            ))
        return flags

    def _check_repetition(self, text: str) -> List[SafetyFlag]:
        flags: List[SafetyFlag] = []
        words = text.lower().split()
        if len(words) < 5:
            return flags
        # Check for repeated consecutive words
        for i in range(len(words) - 1):
            if words[i] == words[i + 1] and len(words[i]) >= 2:
                flags.append(SafetyFlag(
                    category="spam", subcategory="repetition",
                    severity="low", confidence=0.7,
                    matched_text=f"repeated word: '{words[i]}'",
                    description="Repeated word detected",
                    suggestion="Remove duplicate word",
                ))
                break  # Only report once
        return flags

    def _check_urgency(self, text: str) -> List[SafetyFlag]:
        flags: List[SafetyFlag] = []
        for pattern in URGENCY_PATTERNS:
            for match in pattern.finditer(text):
                flags.append(SafetyFlag(
                    category="spam", subcategory="urgency_manipulation",
                    severity="medium", confidence=0.65,
                    matched_text=match.group(),
                    description="Urgency manipulation detected",
                    suggestion="Remove artificial urgency to build genuine trust",
                ))
        return flags

    def _check_misleading(self, text: str) -> List[SafetyFlag]:
        flags: List[SafetyFlag] = []
        for pattern in MISLEADING_PATTERNS:
            for match in pattern.finditer(text):
                flags.append(SafetyFlag(
                    category="spam", subcategory="misleading_claim",
                    severity="high", confidence=0.75,
                    matched_text=match.group(),
                    description="Potentially misleading claim detected",
                    suggestion="Add supporting evidence or soften the claim",
                ))
        return flags

    @property
    def check_count(self) -> int:
        return self._check_count
