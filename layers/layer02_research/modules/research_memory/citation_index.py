"""
Citation Index
Layer 2: Research Engine — Module 7

Indexes citations for quick lookup and cross-referencing:
- Citation storage
- Source-based lookup
- Claim-citation mapping
- Citation frequency analysis
"""

from collections import defaultdict
from typing import Dict, List, Optional


class CitationRecord:
    """A citation record in the index."""

    __slots__ = ("citation_id", "source_name", "source_url", "claim_ids",
                 "credibility", "times_cited", "first_cited", "last_cited")

    def __init__(self, citation_id: str, source_name: str = "", source_url: str = "",
                 credibility: float = 0.5):
        self.citation_id = citation_id
        self.source_name = source_name
        self.source_url = source_url
        self.claim_ids: List[str] = []
        self.credibility = max(0.0, min(1.0, credibility))
        self.times_cited = 0
        self.first_cited = ""
        self.last_cited = ""

    def to_dict(self) -> dict:
        return {
            "citation_id": self.citation_id, "source_name": self.source_name,
            "source_url": self.source_url, "claim_ids": self.claim_ids,
            "credibility": self.credibility, "times_cited": self.times_cited,
        }


class CitationIndex:
    """Index for citations."""

    def __init__(self):
        self._citations: Dict[str, CitationRecord] = {}
        self._source_index: Dict[str, List[str]] = defaultdict(list)
        self._claim_index: Dict[str, List[str]] = defaultdict(list)

    def add(self, citation_id: str, source_name: str = "", source_url: str = "",
            claim_id: str = "", credibility: float = 0.5) -> CitationRecord:
        if citation_id not in self._citations:
            self._citations[citation_id] = CitationRecord(citation_id, source_name, source_url, credibility)
        rec = self._citations[citation_id]
        rec.times_cited += 1
        if claim_id and claim_id not in rec.claim_ids:
            rec.claim_ids.append(claim_id)
            self._claim_index[claim_id].append(citation_id)
        if source_name:
            self._source_index[source_name.lower()].append(citation_id)
        return rec

    def get(self, citation_id: str) -> Optional[CitationRecord]:
        return self._citations.get(citation_id)

    def get_by_source(self, source_name: str) -> List[CitationRecord]:
        cids = self._source_index.get(source_name.lower(), [])
        return [self._citations[cid] for cid in cids if cid in self._citations]

    def get_by_claim(self, claim_id: str) -> List[CitationRecord]:
        cids = self._claim_index.get(claim_id, [])
        return [self._citations[cid] for cid in cids if cid in self._citations]

    def get_most_cited(self, count: int = 10) -> List[CitationRecord]:
        return sorted(self._citations.values(), key=lambda c: c.times_cited, reverse=True)[:count]

    def get_top_sources(self, count: int = 10) -> List[str]:
        source_counts = defaultdict(int)
        for rec in self._citations.values():
            source_counts[rec.source_name] += rec.times_cited
        return [s for s, _ in sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:count]]

    def size(self) -> int:
        return len(self._citations)
