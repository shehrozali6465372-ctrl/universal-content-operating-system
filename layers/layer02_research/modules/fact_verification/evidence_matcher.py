"""
Evidence Matcher
Layer 2: Research Engine — Module 6

Matches claims against evidence from the knowledge base:
- Keyword overlap scoring
- Semantic similarity (Jaccard)
- Entity matching
- Date/number matching
- Evidence ranking
"""

from typing import Dict, List
from layers.layer02_research.modules.fact_verification.claim_extractor import Claim


class EvidenceMatch:
    """A single evidence match for a claim."""

    __slots__ = (
        "match_id", "claim_id", "evidence_text",
        "evidence_source", "similarity_score",
        "keyword_overlap", "supports", "evidence_entry_id",
    )

    def __init__(
        self,
        claim_id: str,
        evidence_text: str,
        evidence_source: str = "",
        similarity_score: float = 0.0,
        keyword_overlap: float = 0.0,
        supports: bool = True,
        evidence_entry_id: str = "",
    ):
        self.match_id = f"match_{hash(claim_id + evidence_text) % 1000000}"
        self.claim_id = claim_id
        self.evidence_text = evidence_text
        self.evidence_source = evidence_source
        self.similarity_score = max(0.0, min(1.0, similarity_score))
        self.keyword_overlap = max(0.0, min(1.0, keyword_overlap))
        self.supports = supports
        self.evidence_entry_id = evidence_entry_id

    def to_dict(self) -> dict:
        return {
            "match_id": self.match_id, "claim_id": self.claim_id,
            "evidence_text": self.evidence_text[:200],
            "evidence_source": self.evidence_source,
            "similarity_score": self.similarity_score,
            "keyword_overlap": self.keyword_overlap,
            "supports": self.supports,
            "evidence_entry_id": self.evidence_entry_id,
        }


# Common stop words for keyword matching
_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "and", "but", "or", "if", "this", "that", "these", "those", "it",
    "its", "not", "no", "so", "than", "too", "very", "just",
}


class EvidenceMatcher:
    """Match claims against evidence from knowledge base."""

    def __init__(self, min_similarity: float = 0.2, min_keyword_overlap: float = 0.15):
        self._min_similarity = min_similarity
        self._min_keyword_overlap = min_keyword_overlap

    def match(
        self,
        claim: Claim,
        evidence_texts: List[Dict[str, str]],
        top_n: int = 5,
    ) -> List[EvidenceMatch]:
        """Match a claim against a list of evidence texts."""
        matches = []
        claim_keywords = self._extract_keywords(claim.text)

        for ev in evidence_texts:
            ev_text = ev.get("text", "")
            ev_source = ev.get("source", "")
            ev_id = ev.get("entry_id", "")

            similarity = self._jaccard_similarity(claim.text, ev_text)
            keyword_overlap = self._keyword_overlap(claim_keywords, ev_text)

            if similarity >= self._min_similarity or keyword_overlap >= self._min_keyword_overlap:
                supports = self._determine_support(claim.text, ev_text)
                matches.append(EvidenceMatch(
                    claim_id=claim.claim_id,
                    evidence_text=ev_text,
                    evidence_source=ev_source,
                    similarity_score=similarity,
                    keyword_overlap=keyword_overlap,
                    supports=supports,
                    evidence_entry_id=ev_id,
                ))

        # Sort by combined score
        matches.sort(key=lambda m: (m.similarity_score * 0.5 + m.keyword_overlap * 0.5), reverse=True)
        return matches[:top_n]

    def match_batch(
        self,
        claims: List[Claim],
        evidence_texts: List[Dict[str, str]],
        top_n: int = 5,
    ) -> Dict[str, List[EvidenceMatch]]:
        """Match multiple claims against evidence."""
        results = {}
        for claim in claims:
            results[claim.claim_id] = self.match(claim, evidence_texts, top_n)
        return results

    def _jaccard_similarity(self, text_a: str, text_b: str) -> float:
        """Jaccard similarity between two texts."""
        words_a = set(text_a.lower().split()) - _STOP_WORDS
        words_b = set(text_b.lower().split()) - _STOP_WORDS
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union) if union else 0.0

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return [w for w in words if w not in _STOP_WORDS]

    def _keyword_overlap(self, claim_keywords: List[str], evidence_text: str) -> float:
        """Calculate keyword overlap between claim keywords and evidence."""
        if not claim_keywords:
            return 0.0
        ev_words = set(evidence_text.lower().split())
        matches = sum(1 for kw in claim_keywords if kw in ev_words)
        return matches / len(claim_keywords) if claim_keywords else 0.0

    def _determine_support(self, claim_text: str, evidence_text: str) -> bool:
        """Determine if evidence supports or contradicts the claim."""
        # Simple heuristic: look for negation patterns
        negation_patterns = [
            r'\bnot\b', r'\bno\b', r'\bnever\b', r'\bneither\b',
            r'\bdoesn\'t\b', r'\bdon\'t\b', r'\bwon\'t\b', r'\bcannot\b',
            r'\bfalse\b', r'\bincorrect\b', r'\bwrong\b', r'\bmyth\b',
        ]
        import re
        ev_lower = evidence_text.lower()
        claim_lower = claim_text.lower()

        ev_negations = sum(1 for p in negation_patterns if re.search(p, ev_lower))
        claim_negations = sum(1 for p in negation_patterns if re.search(p, claim_lower))

        # If both have negation or neither has negation, likely supports
        if ev_negations == claim_negations:
            return True
        # If evidence has negation but claim doesn't (or vice versa), likely contradicts
        if ev_negations > 0 and claim_negations == 0:
            return False
        return True


import re  # Needed for _determine_support
