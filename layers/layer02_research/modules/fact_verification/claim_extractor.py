"""
Claim Extractor
Layer 2: Research Engine — Module 6

Extracts verifiable claims from text:
- Statistical claims (numbers, percentages, dates)
- Causal claims (X causes Y)
- Comparative claims (X is better than Y)
- Trend claims (X is increasing/decreasing)
- Existential claims (X exists, X is real)
"""

import re
from typing import List, Tuple


class Claim:
    """A single extracted claim."""

    __slots__ = (
        "claim_id", "text", "claim_type", "subject",
        "predicate", "object_value", "confidence",
        "source_text", "position",
    )

    CLAIM_TYPES = [
        "statistical", "causal", "comparative", "trend",
        "existential", "definitional", "general",
    ]

    def __init__(
        self,
        text: str,
        claim_type: str = "general",
        subject: str = "",
        predicate: str = "",
        object_value: str = "",
        confidence: float = 0.5,
        source_text: str = "",
        position: int = 0,
    ):
        self.claim_id = f"claim_{hash(text) % 1000000}"
        self.text = text.strip()
        self.claim_type = claim_type if claim_type in self.CLAIM_TYPES else "general"
        self.subject = subject
        self.predicate = predicate
        self.object_value = object_value
        self.confidence = max(0.0, min(1.0, confidence))
        self.source_text = source_text
        self.position = position

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id, "text": self.text,
            "claim_type": self.claim_type, "subject": self.subject,
            "predicate": self.predicate, "object_value": self.object_value,
            "confidence": self.confidence, "source_text": self.source_text,
            "position": self.position,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Claim":
        return cls(
            text=data.get("text", ""), claim_type=data.get("claim_type", "general"),
            subject=data.get("subject", ""), predicate=data.get("predicate", ""),
            object_value=data.get("object_value", ""),
            confidence=data.get("confidence", 0.5),
            source_text=data.get("source_text", ""),
            position=data.get("position", 0),
        )


# Patterns for different claim types
STAT_PATTERNS = [
    re.compile(r'(\d+(?:\.\d+)?)\s*%', re.IGNORECASE),
    re.compile(r'(?:increased|decreased|grew|fell|rose|dropped)\s+by\s+(\d+(?:\.\d+)?)\s*%', re.IGNORECASE),
    re.compile(r'\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:million|billion|trillion)?', re.IGNORECASE),
    re.compile(r'(\d+(?:,\d{3})*)\s+(?:users|people|customers|companies|employees)', re.IGNORECASE),
]

TREND_PATTERNS = [
    re.compile(r'\b(\w+)\s+(?:is|are)\s+(?:increasing|decreasing|growing|declining|rising|falling)', re.IGNORECASE),
    re.compile(r'(?:trend|surge|boom|slump|drop)\s+(?:in|of)\s+(\w+)', re.IGNORECASE),
]

CAUSAL_PATTERNS = [
    re.compile(r'(\w+(?:\s+\w+)?)\s+(?:causes?|leads?\s+to|results?\s+in|triggers?)\s+(\w+(?:\s+\w+)?)', re.IGNORECASE),
    re.compile(r'(?:because|due\s+to|as\s+a\s+result\s+of)\s+(\w+(?:\s+\w+)?)', re.IGNORECASE),
]

COMPARATIVE_PATTERNS = [
    re.compile(r'(\w+(?:\s+\w+)?)\s+(?:is|are)\s+(?:better|worse|faster|slower|more|less|higher|lower)\s+than\s+(\w+(?:\s+\w+)?)', re.IGNORECASE),
]


class ClaimExtractor:
    """Extract verifiable claims from text."""

    def __init__(self, min_claim_length: int = 10, max_claims: int = 20):
        self._min_claim_length = min_claim_length
        self._max_claims = max_claims

    def extract(self, text: str) -> List[Claim]:
        """Extract all claims from text."""
        claims = []
        sentences = self._split_sentences(text)

        for i, sentence in enumerate(sentences):
            if len(sentence.strip()) < self._min_claim_length:
                continue

            claim_type = self._classify_claim(sentence)
            if claim_type == "general":
                # Only extract general claims if they're substantive
                if not self._is_substantive(sentence):
                    continue

            subject, predicate, obj = self._parse_triple(sentence)

            claim = Claim(
                text=sentence.strip(),
                claim_type=claim_type,
                subject=subject,
                predicate=predicate,
                object_value=obj,
                confidence=self._estimate_claim_confidence(sentence, claim_type),
                source_text=text,
                position=text.find(sentence),
            )
            claims.append(claim)

            if len(claims) >= self._max_claims:
                break

        return claims

    def extract_statistical(self, text: str) -> List[Claim]:
        """Extract only statistical claims."""
        return [c for c in self.extract(text) if c.claim_type == "statistical"]

    def extract_trends(self, text: str) -> List[Claim]:
        """Extract only trend claims."""
        return [c for c in self.extract(text) if c.claim_type == "trend"]

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]

    def _classify_claim(self, sentence: str) -> str:
        """Classify the type of claim."""
        for pattern in STAT_PATTERNS:
            if pattern.search(sentence):
                return "statistical"
        for pattern in TREND_PATTERNS:
            if pattern.search(sentence):
                return "trend"
        for pattern in CAUSAL_PATTERNS:
            if pattern.search(sentence):
                return "causal"
        for pattern in COMPARATIVE_PATTERNS:
            if pattern.search(sentence):
                return "comparative"
        return "general"

    def _parse_triple(self, sentence: str) -> Tuple[str, str, str]:
        """Simple subject-predicate-object extraction."""
        words = sentence.split()
        if len(words) < 3:
            return sentence, "", ""
        # Simple heuristic: first 2 words = subject, verb = predicate, rest = object
        mid = len(words) // 2
        subject = " ".join(words[:mid])
        predicate = words[mid] if mid < len(words) else ""
        obj = " ".join(words[mid + 1:])
        return subject, predicate, obj

    def _estimate_claim_confidence(self, sentence: str, claim_type: str) -> float:
        """Estimate how likely this claim is to be verifiable."""
        base = {
            "statistical": 0.7, "trend": 0.6, "causal": 0.5,
            "comparative": 0.5, "existential": 0.6, "definitional": 0.8,
            "general": 0.4,
        }.get(claim_type, 0.4)

        # Boost for specific numbers
        if re.search(r'\d+', sentence):
            base += 0.1
        # Boost for hedging words (less verifiable)
        if re.search(r'\b(might|could|possibly|perhaps|maybe)\b', sentence, re.IGNORECASE):
            base -= 0.15

        return max(0.1, min(1.0, base))

    def _is_substantive(self, sentence: str) -> bool:
        """Check if a sentence contains a substantive claim."""
        words = sentence.split()
        return len(words) >= 6 and bool(re.search(r'\b(is|are|was|were|has|have|will|can)\b', sentence, re.IGNORECASE))
