"""
Entity Linker — Sprint 2 (v2.0)

Links extracted entities to known knowledge base entries.
Provides entity normalization, type classification, and confidence scoring.

Public API:
    link(entities, text) -> List[LinkedEntity]
    normalize(entity_text) -> str
    classify(entity_text, context) -> str
    confidence(entity_text, entity_type) -> float
    get_entity_links(entity_text) -> List[Dict]

Version: 2.0.0
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Set


# ─────────────────────────────────────────────────────────────────────
# Entity Type Taxonomy
# ─────────────────────────────────────────────────────────────────────
class EntityType:
    """Canonical entity type constants."""
    PERSON = "PERSON"
    ORGANIZATION = "ORG"
    LOCATION = "LOC"
    DATE = "DATE"
    MONEY = "MONEY"
    NUMBER = "NUMBER"
    URL = "URL"
    EMAIL = "EMAIL"
    HASHTAG = "HASHTAG"
    MENTION = "MENTION"
    PRODUCT = "PRODUCT"
    EVENT = "EVENT"
    TECHNOLOGY = "TECH"
    UNKNOWN = "UNKNOWN"


# Known entities knowledge base (expandable)
_KNOWN_ORGS: Dict[str, Dict] = {
    "facebook": {"canonical": "Facebook (Meta)", "aliases": ["meta", "fb"], "confidence": 0.99},
    "google": {"canonical": "Google (Alphabet)", "aliases": ["alphabet"], "confidence": 0.99},
    "microsoft": {"canonical": "Microsoft Corporation", "aliases": ["msft"], "confidence": 0.99},
    "apple": {"canonical": "Apple Inc.", "aliases": [], "confidence": 0.99},
    "amazon": {"canonical": "Amazon.com Inc.", "aliases": ["aws"], "confidence": 0.99},
    "openai": {"canonical": "OpenAI", "aliases": ["gpt", "chatgpt"], "confidence": 0.99},
    "tesla": {"canonical": "Tesla Inc.", "aliases": [], "confidence": 0.99},
    "meta": {"canonical": "Meta Platforms", "aliases": ["facebook"], "confidence": 0.98},
    "netflix": {"canonical": "Netflix Inc.", "aliases": [], "confidence": 0.99},
    "samsung": {"canonical": "Samsung Electronics", "aliases": [], "confidence": 0.99},
    "nvidia": {"canonical": "NVIDIA Corporation", "aliases": [], "confidence": 0.99},
    "twitter": {"canonical": "X (Twitter)", "aliases": ["x"], "confidence": 0.97},
    "linkedin": {"canonical": "LinkedIn (Microsoft)", "aliases": [], "confidence": 0.99},
    "youtube": {"canonical": "YouTube (Google)", "aliases": [], "confidence": 0.99},
    "github": {"canonical": "GitHub (Microsoft)", "aliases": [], "confidence": 0.99},
    "anthropic": {"canonical": "Anthropic", "aliases": ["claude"], "confidence": 0.98},
    "deepseek": {"canonical": "DeepSeek", "aliases": [], "confidence": 0.97},
}

_KNOWN_TECH: Dict[str, Dict] = {
    "python": {"canonical": "Python", "category": "programming_language", "confidence": 0.99},
    "javascript": {"canonical": "JavaScript", "category": "programming_language", "confidence": 0.99},
    "gpt": {"canonical": "GPT (Generative Pre-trained Transformer)", "category": "ai_model", "confidence": 0.98},
    "gpt-4": {"canonical": "GPT-4", "category": "ai_model", "confidence": 0.99},
    "gpt-5": {"canonical": "GPT-5", "category": "ai_model", "confidence": 0.98},
    "claude": {"canonical": "Claude", "category": "ai_model", "confidence": 0.98},
    "gemini": {"canonical": "Gemini (Google)", "category": "ai_model", "confidence": 0.97},
    "react": {"canonical": "React", "category": "framework", "confidence": 0.97},
    "tensorflow": {"canonical": "TensorFlow", "category": "ml_framework", "confidence": 0.99},
    "pytorch": {"canonical": "PyTorch", "category": "ml_framework", "confidence": 0.99},
    "docker": {"canonical": "Docker", "category": "devops_tool", "confidence": 0.99},
    "kubernetes": {"canonical": "Kubernetes", "category": "devops_tool", "confidence": 0.99},
    "bitcoin": {"canonical": "Bitcoin", "category": "cryptocurrency", "confidence": 0.99},
    "ethereum": {"canonical": "Ethereum", "category": "cryptocurrency", "confidence": 0.99},
    "ai": {"canonical": "Artificial Intelligence", "category": "field", "confidence": 0.95},
    "ml": {"canonical": "Machine Learning", "category": "field", "confidence": 0.95},
    "nlp": {"canonical": "Natural Language Processing", "category": "field", "confidence": 0.98},
    "llm": {"canonical": "Large Language Model", "category": "field", "confidence": 0.97},
}

_KNOWN_PERSONS: Dict[str, Dict] = {
    "elon musk": {"canonical": "Elon Musk", "roles": ["CEO of Tesla, SpaceX"], "confidence": 0.99},
    "sam altman": {"canonical": "Sam Altman", "roles": ["CEO of OpenAI"], "confidence": 0.99},
    "sundar pichai": {"canonical": "Sundar Pichai", "roles": ["CEO of Google/Alphabet"], "confidence": 0.99},
    "satya nadella": {"canonical": "Satya Nadella", "roles": ["CEO of Microsoft"], "confidence": 0.99},
    "mark zuckerberg": {"canonical": "Mark Zuckerberg", "roles": ["CEO of Meta"], "confidence": 0.99},
    "jensen huang": {"canonical": "Jensen Huang", "roles": ["CEO of NVIDIA"], "confidence": 0.99},
    "tim cook": {"canonical": "Tim Cook", "roles": ["CEO of Apple"], "confidence": 0.99},
    "jeff bezos": {"canonical": "Jeff Bezos", "roles": ["Founder of Amazon"], "confidence": 0.99},
}

_KNOWN_LOCATIONS: Dict[str, Dict] = {
    "san francisco": {"canonical": "San Francisco, CA", "country": "US", "confidence": 0.99},
    "new york": {"canonical": "New York City, NY", "country": "US", "confidence": 0.99},
    "london": {"canonical": "London", "country": "UK", "confidence": 0.99},
    "tokyo": {"canonical": "Tokyo", "country": "JP", "confidence": 0.99},
    "paris": {"canonical": "Paris", "country": "FR", "confidence": 0.99},
    "berlin": {"canonical": "Berlin", "country": "DE", "confidence": 0.99},
    "dubai": {"canonical": "Dubai", "country": "AE", "confidence": 0.99},
    "singapore": {"canonical": "Singapore", "country": "SG", "confidence": 0.99},
    "bangalore": {"canonical": "Bangalore", "country": "IN", "confidence": 0.98},
    "lahore": {"canonical": "Lahore", "country": "PK", "confidence": 0.98},
    "karachi": {"canonical": "Karachi", "country": "PK", "confidence": 0.98},
    "islamabad": {"canonical": "Islamabad", "country": "PK", "confidence": 0.99},
}


# ─────────────────────────────────────────────────────────────────────
# Linked Entity Model
# ─────────────────────────────────────────────────────────────────────
class LinkedEntity:
    """An entity linked to the knowledge base with confidence.

    Attributes:
        text: Original entity text from source.
        entity_type: Canonical entity type (PERSON, ORG, etc.).
        canonical: Normalized canonical name (if found in KB).
        confidence: Linking confidence (0.0–1.0).
        source: Where the entity was found (text, KB, alias).
        metadata: Additional info (roles, category, country, etc.).
    """

    __slots__ = ("text", "entity_type", "canonical", "confidence", "source", "metadata")

    def __init__(
        self,
        text: str,
        entity_type: str = EntityType.UNKNOWN,
        canonical: str = "",
        confidence: float = 0.5,
        source: str = "text",
        metadata: Optional[Dict] = None,
    ) -> None:
        self.text = text
        self.entity_type = entity_type
        self.canonical = canonical or text
        self.confidence = confidence
        self.source = source
        self.metadata = metadata or {}

    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "entity_type": self.entity_type,
            "canonical": self.canonical,
            "confidence": round(self.confidence, 3),
            "source": self.source,
            "metadata": dict(self.metadata),
        }

    def __repr__(self) -> str:
        return (
            f"LinkedEntity('{self.text}', type={self.entity_type}, "
            f"canonical='{self.canonical}', conf={self.confidence:.2f})"
        )


# ─────────────────────────────────────────────────────────────────────
# Entity Linker
# ─────────────────────────────────────────────────────────────────────
class EntityLinker:
    """Links raw entities to the knowledge base with confidence scoring.

    Usage::

        linker = EntityLinker()
        linked = linker.link(entities, "OpenAI released GPT-5")
        for e in linked:
            print(e.canonical, e.confidence)
    """

    def __init__(self, custom_kb: Optional[Dict[str, Dict[str, Dict]]] = None) -> None:
        """
        Args:
            custom_kb: Optional custom knowledge base override.
                       Format: {"ORG": {"name": {...}}, "TECH": {...}}
        """
        if custom_kb:
            self._org_kb = custom_kb.get("ORG", _KNOWN_ORGS)
            self._tech_kb = custom_kb.get("TECH", _KNOWN_TECH)
            self._person_kb = custom_kb.get("PERSON", _KNOWN_PERSONS)
            self._loc_kb = custom_kb.get("LOC", _KNOWN_LOCATIONS)
        else:
            self._org_kb = dict(_KNOWN_ORGS)
            self._tech_kb = dict(_KNOWN_TECH)
            self._person_kb = dict(_KNOWN_PERSONS)
            self._loc_kb = dict(_KNOWN_LOCATIONS)

    def link(self, entities: List[Dict], text: str = "") -> List[LinkedEntity]:
        """Link a list of raw entities to the knowledge base.

        Args:
            entities: List of dicts with 'text' and 'type' keys
                      (as produced by SemanticAnalyzer._extract_entities).
            text: Original text for context.

        Returns:
            List of LinkedEntity objects with canonical names and confidence.
        """
        linked: List[LinkedEntity] = []
        seen: Set[str] = set()

        for ent in entities:
            raw_text = ent.get("text", "")
            raw_type = ent.get("type", "unknown")
            key = raw_text.lower().strip()

            if key in seen:
                continue
            seen.add(key)

            # Try to link against knowledge bases
            result = self._link_single(raw_text, raw_type, text)
            linked.append(result)

        return linked

    def normalize(self, entity_text: str) -> str:
        """Normalize entity text to canonical form.

        Examples:
            "openai" -> "OpenAI"
            "gpt4" -> "GPT-4"
            "sf" -> "San Francisco"
        """
        lower = entity_text.lower().strip()

        # Check all knowledge bases
        for kb in [self._org_kb, self._tech_kb, self._person_kb, self._loc_kb]:
            if lower in kb:
                return kb[lower]["canonical"]
            # Check aliases
            for name, info in kb.items():
                if lower in info.get("aliases", []):
                    return info["canonical"]

        # Default: title-case
        return entity_text.strip().title()

    def classify(self, entity_text: str, context: str = "") -> str:
        """Classify entity text into the most likely type.

        Args:
            entity_text: Raw entity text.
            context: Surrounding text for disambiguation.

        Returns:
            Entity type string (PERSON, ORG, TECH, LOC, etc.)
        """
        lower = entity_text.lower().strip()
        ctx_lower = context.lower()

        # Check knowledge bases first
        if lower in self._org_kb or any(lower in v.get("aliases", []) for v in self._org_kb.values()):
            return EntityType.ORGANIZATION
        if lower in self._tech_kb or any(lower in v.get("aliases", []) for v in self._tech_kb.values()):
            return EntityType.TECHNOLOGY
        if lower in self._person_kb:
            return EntityType.PERSON
        if lower in self._loc_kb:
            return EntityType.LOCATION

        # Pattern-based fallback
        if re.match(r"https?://", entity_text):
            return EntityType.URL
        if "@" in entity_text and "." in entity_text:
            return EntityType.EMAIL
        if entity_text.startswith("#"):
            return EntityType.HASHTAG
        if entity_text.startswith("@"):
            return EntityType.MENTION
        if re.match(r"\$[\d,]+", entity_text):
            return EntityType.MONEY
        if re.match(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", entity_text):
            return EntityType.DATE
        if re.match(r"^[A-Z][a-z]+ [A-Z][a-z]+$", entity_text):
            return EntityType.PERSON

        # Context-based hints
        if any(w in ctx_lower for w in ["ceo", "founder", "president", "author"]):
            return EntityType.PERSON
        if any(w in ctx_lower for w in ["company", "corporation", "startup", "firm"]):
            return EntityType.ORGANIZATION

        return EntityType.UNKNOWN

    def confidence(self, entity_text: str, entity_type: str = "") -> float:
        """Compute linking confidence for an entity.

        Confidence is higher when:
        - Entity is found in the knowledge base
        - Entity type is certain (pattern match)
        - Entity text is unambiguous (not a common word)
        """
        lower = entity_text.lower().strip()

        # Exact KB match → high confidence
        for kb in [self._org_kb, self._tech_kb, self._person_kb, self._loc_kb]:
            if lower in kb:
                return kb[lower].get("confidence", 0.9)
            for name, info in kb.items():
                if lower in info.get("aliases", []):
                    return info.get("confidence", 0.85) * 0.95  # Slight penalty for alias

        # Type-specific pattern confidence
        type_confidence = {
            EntityType.URL: 0.95,
            EntityType.EMAIL: 0.95,
            EntityType.HASHTAG: 0.90,
            EntityType.MENTION: 0.85,
            EntityType.MONEY: 0.90,
            EntityType.DATE: 0.85,
            EntityType.PERSON: 0.60,  # Pattern match, not KB
        }

        if entity_type in type_confidence:
            return type_confidence[entity_type]

        # Heuristic: capitalized multi-word = likely a name
        if re.match(r"^[A-Z][a-z]+ [A-Z][a-z]+$", entity_text):
            return 0.55

        # Unknown entity → low confidence
        return 0.3

    def get_entity_links(self, entity_text: str) -> List[Dict]:
        """Find all possible knowledge base links for an entity.

        Returns multiple matches ranked by confidence.
        """
        lower = entity_text.lower().strip()
        matches: List[Dict] = []

        all_kbs = [
            ("ORG", self._org_kb),
            ("TECH", self._tech_kb),
            ("PERSON", self._person_kb),
            ("LOC", self._loc_kb),
        ]

        for kb_type, kb in all_kbs:
            if lower in kb:
                info = kb[lower]
                matches.append({
                    "type": kb_type,
                    "canonical": info["canonical"],
                    "confidence": info.get("confidence", 0.5),
                    "metadata": {k: v for k, v in info.items() if k not in ("canonical", "confidence")},
                })
            # Check aliases
            for name, info in kb.items():
                if lower in info.get("aliases", []):
                    matches.append({
                        "type": kb_type,
                        "canonical": info["canonical"],
                        "confidence": info.get("confidence", 0.5) * 0.9,
                        "metadata": {"alias_of": name},
                    })

        matches.sort(key=lambda m: -m["confidence"])
        return matches

    def add_entity(self, entity_type: str, name: str, info: Dict) -> None:
        """Add an entity to the knowledge base at runtime."""
        kb_map = {
            "ORG": self._org_kb,
            "TECH": self._tech_kb,
            "PERSON": self._person_kb,
            "LOC": self._loc_kb,
        }
        kb = kb_map.get(entity_type)
        if kb:
            kb[name.lower()] = info

    def get_kb_stats(self) -> Dict[str, int]:
        """Get knowledge base size per type."""
        return {
            "ORG": len(self._org_kb),
            "TECH": len(self._tech_kb),
            "PERSON": len(self._person_kb),
            "LOC": len(self._loc_kb),
        }

    # ── Private ──────────────────────────────────────────────────────

    def _link_single(self, raw_text: str, raw_type: str, context: str) -> LinkedEntity:
        """Link a single entity."""
        lower = raw_text.lower().strip()

        # Determine type
        entity_type = self.classify(raw_text, context)

        # Find canonical name and KB confidence
        canonical = raw_text
        kb_confidence = 0.0
        source = "pattern"
        metadata: Dict = {}

        for kb_name, kb in [("ORG", self._org_kb), ("TECH", self._tech_kb),
                            ("PERSON", self._person_kb), ("LOC", self._loc_kb)]:
            if lower in kb:
                info = kb[lower]
                canonical = info["canonical"]
                kb_confidence = info.get("confidence", 0.5)
                source = "knowledge_base"
                entity_type = kb_name
                metadata = {k: v for k, v in info.items() if k not in ("canonical", "confidence")}
                break
            # Check aliases
            for name, info in kb.items():
                if lower in info.get("aliases", []):
                    canonical = info["canonical"]
                    kb_confidence = info.get("confidence", 0.5) * 0.9
                    source = "alias"
                    entity_type = kb_name
                    metadata = {"alias_of": name}
                    break
            if source != "pattern":
                break

        # Final confidence
        final_confidence = kb_confidence if kb_confidence > 0 else self.confidence(raw_text, entity_type)

        return LinkedEntity(
            text=raw_text,
            entity_type=entity_type,
            canonical=canonical,
            confidence=round(final_confidence, 3),
            source=source,
            metadata=metadata,
        )
