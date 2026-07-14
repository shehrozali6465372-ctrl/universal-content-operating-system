"""
Entity Recognizer
Extracts named entities from text (people, organizations, locations, etc.)
Using pattern-based recognition (no external NLP library needed).
"""

import re
from typing import Dict, List, Optional, Set


# Entity type patterns
ENTITY_PATTERNS: Dict[str, List[str]] = {
    "person": [
        r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",  # John Smith
        r"\b(?:Mr|Mrs|Ms|Dr|Prof)\.?\s+[A-Z][a-z]+\b",
    ],
    "organization": [
        r"\b(?:Facebook|Google|Microsoft|Apple|Amazon|OpenAI|Tesla|Meta)\b",
        r"\b[A-Z][a-z]+(?:Inc|Corp|Ltd|LLC|Co)\b",
    ],
    "location": [
        r"\b(?:New York|Los Angeles|San Francisco|London|Tokyo|Paris|Berlin|Dubai|India|Pakistan)\b",
        r"\b[A-Z][a-z]+(?:ville|town|city|land|stan)\b",
    ],
    "url": [
        r"https?://[^\s]+",
        r"www\.[^\s]+",
    ],
    "email": [
        r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
    ],
    "hashtag": [
        r"#[a-zA-Z0-9_]+",
    ],
    "mention": [
        r"@[a-zA-Z0-9_]+",
    ],
    "number": [
        r"\b\d+(?:,\d{3})*(?:\.\d+)?%?\b",
    ],
    "date": [
        r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}\b",
    ],
    "money": [
        r"\$[\d,]+(?:\.\d{2})?",
        r"[\d,]+(?:USD|EUR|GBP|PKR)",
    ],
}


class Entity:
    """A recognized entity."""

    __slots__ = ("text", "entity_type", "start", "end", "confidence")

    def __init__(self, text: str, entity_type: str, start: int = 0, end: int = 0, confidence: float = 0.8):
        self.text = text
        self.entity_type = entity_type
        self.start = start
        self.end = end
        self.confidence = confidence

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "type": self.entity_type,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
        }

    def __repr__(self) -> str:
        return f"Entity('{self.text}', type={self.entity_type})"


class EntityRecognizer:
    """Recognizes named entities in text using pattern matching."""

    def __init__(self):
        self._patterns: Dict[str, List[re.Pattern]] = {}
        for etype, pattern_strs in ENTITY_PATTERNS.items():
            self._patterns[etype] = [re.compile(p) for p in pattern_strs]

    def recognize(self, text: str) -> List[Entity]:
        """Recognize all entities in text."""
        entities: List[Entity] = []
        seen: Set[str] = set()

        for etype, patterns in self._patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    entity_text = match.group()
                    # Deduplicate
                    key = f"{entity_text.lower()}:{etype}"
                    if key not in seen:
                        seen.add(key)
                        entities.append(Entity(
                            text=entity_text,
                            entity_type=etype,
                            start=match.start(),
                            end=match.end(),
                        ))

        return entities

    def recognize_by_type(self, text: str, entity_type: str) -> List[Entity]:
        """Recognize only entities of a specific type."""
        return [e for e in self.recognize(text) if e.entity_type == entity_type]

    def get_entity_types(self, text: str) -> Dict[str, int]:
        """Get count of each entity type in text."""
        entities = self.recognize(text)
        counts: Dict[str, int] = {}
        for e in entities:
            counts[e.entity_type] = counts.get(e.entity_type, 0) + 1
        return counts

    def extract_all_text(self, text: str, entity_type: Optional[str] = None) -> List[str]:
        """Extract all entity text values."""
        entities = self.recognize(text)
        if entity_type:
            entities = [e for e in entities if e.entity_type == entity_type]
        return [e.text for e in entities]

    def add_pattern(self, entity_type: str, pattern: str):
        """Add a custom entity pattern."""
        compiled = re.compile(pattern)
        if entity_type not in self._patterns:
            self._patterns[entity_type] = []
        self._patterns[entity_type].append(compiled)
