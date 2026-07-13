"""
Citation Builder
Layer 2: Research Engine — Module 6

Builds citations for verified claims:
- Inline citations
- Reference list generation
- Citation formatting (multiple styles)
- Citation deduplication
"""

from typing import Dict, List, Optional


class Citation:
    """A single citation."""

    __slots__ = (
        "citation_id", "source_name", "source_url",
        "title", "author", "date", "accessed_date",
        "reliability_score", "citation_text",
    )

    def __init__(
        self,
        source_name: str = "",
        source_url: str = "",
        title: str = "",
        author: str = "",
        date: str = "",
        reliability_score: float = 0.5,
    ):
        self.citation_id = f"cite_{hash(source_name + title) % 1000000}"
        self.source_name = source_name
        self.source_url = source_url
        self.title = title
        self.author = author
        self.date = date
        self.accessed_date = ""
        self.reliability_score = max(0.0, min(1.0, reliability_score))
        self.citation_text = self._build_text()

    def _build_text(self) -> str:
        parts = []
        if self.author:
            parts.append(self.author)
        if self.title:
            parts.append(f'"{self.title}"')
        if self.source_name:
            parts.append(self.source_name)
        if self.date:
            parts.append(f"({self.date})")
        if self.source_url:
            parts.append(self.source_url)
        return ". ".join(parts) + "." if parts else "Unknown source."

    def to_dict(self) -> dict:
        return {
            "citation_id": self.citation_id,
            "source_name": self.source_name, "source_url": self.source_url,
            "title": self.title, "author": self.author, "date": self.date,
            "accessed_date": self.accessed_date,
            "reliability_score": self.reliability_score,
            "citation_text": self.citation_text,
        }


class CitationBuilder:
    """Build citations for verified claims."""

    FORMATS = ["inline", "apa", "mla", "chicago", "plain"]

    def __init__(self):
        self._citations: Dict[str, Citation] = {}

    def build_citation(
        self,
        source_name: str,
        source_url: str = "",
        title: str = "",
        author: str = "",
        date: str = "",
        reliability_score: float = 0.5,
    ) -> Citation:
        """Create a single citation."""
        citation = Citation(source_name, source_url, title, author, date, reliability_score)
        self._citations[citation.citation_id] = citation
        return citation

    def build_from_evidence(
        self, evidence_entries: List[Dict]
    ) -> List[Citation]:
        """Build citations from evidence entries."""
        citations = []
        for entry in evidence_entries:
            c = self.build_citation(
                source_name=entry.get("source", "Unknown"),
                source_url=entry.get("source_url", ""),
                title=entry.get("title", ""),
                author=entry.get("author", ""),
                date=entry.get("published_at", ""),
                reliability_score=entry.get("credibility_score", 0.5),
            )
            citations.append(c)
        return self._deduplicate_citations(citations)

    def format_citation(self, citation: Citation, style: str = "inline") -> str:
        """Format a citation in a specific style."""
        if style == "apa":
            parts = []
            if citation.author:
                parts.append(citation.author)
            if citation.date:
                parts.append(f"({citation.date})")
            if citation.title:
                parts.append(citation.title)
            if citation.source_name:
                parts.append(citation.source_name)
            return " ".join(parts)

        elif style == "mla":
            parts = []
            if citation.author:
                parts.append(citation.author)
            if citation.title:
                parts.append(f'"{citation.title}"')
            if citation.source_name:
                parts.append(citation.source_name)
            if citation.date:
                parts.append(citation.date)
            return ", ".join(parts)

        elif style == "plain":
            return citation.citation_text

        # Default: inline
        src = citation.source_name or "Unknown"
        if citation.date:
            return f"({src}, {citation.date})"
        return f"({src})"

    def build_reference_list(self, citations: List[Citation], style: str = "apa") -> List[str]:
        """Build a formatted reference list."""
        formatted = [self.format_citation(c, style) for c in citations]
        return sorted(set(formatted))

    def _deduplicate_citations(self, citations: List[Citation]) -> List[Citation]:
        """Remove duplicate citations."""
        seen = set()
        unique = []
        for c in citations:
            key = (c.source_name.lower(), c.title.lower())
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique

    def get_citation(self, citation_id: str) -> Optional[Citation]:
        return self._citations.get(citation_id)

    def list_citations(self) -> List[Citation]:
        return list(self._citations.values())
