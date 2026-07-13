"""
Gap Detector
Layer 2: Research Engine — Module 3

Detects content gaps and weaknesses across competitors:
- Topic gaps (topics no one covers)
- Format gaps (underused formats)
- Audience gaps (neglected segments)
- Time gaps (dead zones)
- Depth gaps (shallow coverage)
- Quality gaps (low effort content)
"""

from typing import Dict, List, Set, Tuple
from layers.layer02_research.modules.competitor_analysis.competitor_profile import CompetitorProfile


class ContentGap:
    """Represents a detected content gap."""

    __slots__ = ("gap_type", "description", "severity", "opportunity_score", "evidence")

    SEVERITY_LEVELS = ["low", "medium", "high", "critical"]

    def __init__(
        self,
        gap_type: str,
        description: str,
        severity: str = "medium",
        opportunity_score: float = 5.0,
        evidence: str = "",
    ):
        self.gap_type = gap_type
        self.description = description
        self.severity = severity if severity in self.SEVERITY_LEVELS else "medium"
        self.opportunity_score = max(0.0, min(10.0, opportunity_score))
        self.evidence = evidence

    def to_dict(self) -> dict:
        return {
            "gap_type": self.gap_type,
            "description": self.description,
            "severity": self.severity,
            "opportunity_score": self.opportunity_score,
            "evidence": self.evidence,
        }


class GapDetector:
    """Detect content gaps across competitors."""

    def __init__(self):
        self._gaps: Dict[str, List[ContentGap]] = {}

    def detect_all(
        self,
        competitors: List[CompetitorProfile],
        known_topics: List[str] = None,
    ) -> List[ContentGap]:
        """Run all gap detection algorithms."""
        all_gaps = []
        all_gaps.extend(self.detect_topic_gaps(competitors, known_topics or []))
        all_gaps.extend(self.detect_format_gaps(competitors))
        all_gaps.extend(self.detect_audience_gaps(competitors))
        all_gaps.extend(self.detect_depth_gaps(competitors))

        # Sort by opportunity score
        all_gaps.sort(key=lambda g: g.opportunity_score, reverse=True)
        return all_gaps

    def detect_topic_gaps(
        self, competitors: List[CompetitorProfile], known_topics: List[str]
    ) -> List[ContentGap]:
        """Find topics that competitors aren't covering."""
        all_competitor_topics: Set[str] = set()
        for comp in competitors:
            all_competitor_topics.update(t.lower() for t in comp.top_topics)

        known_set = set(t.lower() for t in known_topics)
        uncovered = known_set - all_competitor_topics

        gaps = []
        for topic in uncovered:
            gaps.append(ContentGap(
                gap_type="topic",
                description=f"Topic '{topic}' is not covered by any competitor",
                severity="high",
                opportunity_score=8.0,
                evidence=f"0/{len(competitors)} competitors cover this topic",
            ))
        return gaps

    def detect_format_gaps(self, competitors: List[CompetitorProfile]) -> List[ContentGap]:
        """Find underused content formats."""
        all_formats: Dict[str, int] = {}
        for comp in competitors:
            for fmt in comp.top_formats:
                all_formats[fmt] = all_formats.get(fmt, 0) + 1

        common_formats = {f for f, c in all_formats.items() if c >= len(competitors) * 0.5}
        all_possible = {"carousel", "video", "reel", "story", "text_post", "infographic", "live", "poll"}
        underused = all_possible - common_formats

        gaps = []
        for fmt in underused:
            gaps.append(ContentGap(
                gap_type="format",
                description=f"Format '{fmt}' is underused by competitors",
                severity="medium",
                opportunity_score=6.0,
                evidence=f"Only {all_formats.get(fmt, 0)}/{len(competitors)} competitors use it",
            ))
        return gaps

    def detect_audience_gaps(self, competitors: List[CompetitorProfile]) -> List[ContentGap]:
        """Find neglected audience segments."""
        niches_covered = set(comp.niche for comp in competitors)
        niche_counts = {}
        for comp in competitors:
            niche_counts[comp.niche] = niche_counts.get(comp.niche, 0) + 1

        saturated = {n for n, c in niche_counts.items() if c >= 3}
        gaps = []
        for niche in saturated:
            gaps.append(ContentGap(
                gap_type="audience",
                description=f"Niche '{niche}' is saturated — consider sub-niche targeting",
                severity="medium",
                opportunity_score=5.0,
                evidence=f"{niche_counts[niche]} competitors in this niche",
            ))
        return gaps

    def detect_depth_gaps(self, competitors: List[CompetitorProfile]) -> List[ContentGap]:
        """Find competitors with shallow content (few topics)."""
        gaps = []
        for comp in competitors:
            if len(comp.top_topics) < 3 and comp.post_count > 10:
                gaps.append(ContentGap(
                    gap_type="depth",
                    description=f"'{comp.page_name}' has narrow topic focus ({len(comp.top_topics)} topics)",
                    severity="low",
                    opportunity_score=5.5,
                    evidence=f"{comp.post_count} posts but only {len(comp.top_topics)} topics",
                ))
        return gaps

    def get_top_gaps(self, count: int = 5) -> List[ContentGap]:
        """Get top gaps across all detected."""
        all_gaps = []
        for gaps in self._gaps.values():
            all_gaps.extend(gaps)
        all_gaps.sort(key=lambda g: g.opportunity_score, reverse=True)
        return all_gaps[:count]

    def get_gaps_for_competitor(self, competitor_id: str) -> List[ContentGap]:
        return list(self._gaps.get(competitor_id, []))

    def store_gaps(self, competitor_id: str, gaps: List[ContentGap]):
        """Store detected gaps for a competitor."""
        self._gaps[competitor_id] = gaps
