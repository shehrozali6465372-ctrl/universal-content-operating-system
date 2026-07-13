"""
Opportunity Finder
Layer 2: Research Engine — Module 3

Finds actionable opportunities from competitor analysis:
- Weakness exploitation
- Timing opportunities
- Content format innovation
- Audience expansion
- Competitive advantage identification
"""

from typing import Dict, List, Optional
from layers.layer02_research.modules.competitor_analysis.competitor_profile import CompetitorProfile
from layers.layer02_research.modules.competitor_analysis.gap_detector import ContentGap
from layers.layer02_research.modules.competitor_analysis.engagement_analyzer import EngagementAnalyzer
from layers.layer02_research.modules.competitor_analysis.writing_style_analyzer import WritingStyleAnalyzer


class Opportunity:
    """A detected competitive opportunity."""

    __slots__ = (
        "opportunity_id", "opp_type", "description",
        "priority", "effort_level", "impact_score",
        "source_competitors", "action_items",
        "confidence",
    )

    PRIORITIES = ["low", "medium", "high", "critical"]
    EFFORT_LEVELS = ["low", "medium", "high"]

    def __init__(
        self,
        opp_type: str,
        description: str,
        priority: str = "medium",
        effort_level: str = "medium",
        impact_score: float = 5.0,
        source_competitors: Optional[List[str]] = None,
        action_items: Optional[List[str]] = None,
        confidence: float = 0.7,
    ):
        self.opportunity_id = f"opp_{opp_type}_{int(__import__('time').time())}"
        self.opp_type = opp_type
        self.description = description
        self.priority = priority if priority in self.PRIORITIES else "medium"
        self.effort_level = effort_level if effort_level in self.EFFORT_LEVELS else "medium"
        self.impact_score = max(0.0, min(10.0, impact_score))
        self.source_competitors = source_competitors or []
        self.action_items = action_items or []
        self.confidence = max(0.0, min(1.0, confidence))

    def to_dict(self) -> dict:
        return {
            "opportunity_id": self.opportunity_id,
            "opp_type": self.opp_type,
            "description": self.description,
            "priority": self.priority,
            "effort_level": self.effort_level,
            "impact_score": self.impact_score,
            "source_competitors": self.source_competitors,
            "action_items": self.action_items,
            "confidence": self.confidence,
        }


class OpportunityFinder:
    """Find actionable opportunities from competitive analysis."""

    def __init__(self):
        self._opportunities: Dict[str, List[Opportunity]] = {}

    def discover_all(
        self,
        competitors: List[CompetitorProfile],
        engagement_analyzer: Optional[EngagementAnalyzer] = None,
        writing_analyzer: Optional[WritingStyleAnalyzer] = None,
        gaps: Optional[List[ContentGap]] = None,
    ) -> List[Opportunity]:
        """Run all opportunity discovery algorithms."""
        all_opps = []
        all_opps.extend(self._weakness_exploitation(competitors, engagement_analyzer))
        all_opps.extend(self._content_format_innovation(competitors))
        all_opps.extend(self._audience_expansion(competitors))
        all_opps.extend(self._timing_opportunities(competitors))
        all_opps.extend(self._gap_to_opportunity(gaps or []))

        all_opps.sort(key=lambda o: (self._priority_weight(o.priority), o.impact_score), reverse=True)
        return all_opps

    def _weakness_exploitation(
        self, competitors: List[CompetitorProfile], eng_analyzer: Optional[EngagementAnalyzer]
    ) -> List[Opportunity]:
        """Generate opportunities from competitor weaknesses."""
        opportunities = []
        for comp in competitors:
            if not comp.weaknesses:
                continue
            for weakness in comp.weaknesses:
                impact = 7.0 if "declining" in weakness or "low" in weakness else 5.0
                opportunities.append(Opportunity(
                    opp_type="weakness_exploitation",
                    description=f"Competitor '{comp.page_name}' weakness: {weakness}",
                    priority="high" if impact >= 7.0 else "medium",
                    effort_level="low",
                    impact_score=impact,
                    source_competitors=[comp.page_name],
                    action_items=[f"Create content that addresses: {weakness}"],
                    confidence=comp.confidence,
                ))
        return opportunities

    def _content_format_innovation(self, competitors: List[CompetitorProfile]) -> List[Opportunity]:
        """Find format opportunities."""
        all_formats = set()
        for comp in competitors:
            all_formats.update(comp.top_formats)

        new_formats = [f for f in ["reel", "live", "carousel", "poll", "infographic"] if f not in all_formats]
        opps = []
        for fmt in new_formats:
            opps.append(Opportunity(
                opp_type="format_innovation",
                description=f"Use '{fmt}' format that competitors are ignoring",
                priority="high",
                effort_level="medium",
                impact_score=7.5,
                action_items=[f"Create 5 test posts using '{fmt}' format", "Track engagement comparison"],
                confidence=0.7,
            ))
        return opps

    def _audience_expansion(self, competitors: List[CompetitorProfile]) -> List[Opportunity]:
        """Find audience opportunities."""
        niches = set(comp.niche for comp in competitors)
        opps = []
        if "finance" in niches:
            opps.append(Opportunity(
                opp_type="audience_expansion",
                description="Target personal finance beginners — competitors focus on advanced topics",
                priority="medium",
                effort_level="low",
                impact_score=6.5,
                action_items=["Create 'finance for beginners' series"],
                confidence=0.75,
            ))
        if "technology" in niches:
            opps.append(Opportunity(
                opp_type="audience_expansion",
                description="Create non-technical tech content for general audience",
                priority="medium",
                effort_level="low",
                impact_score=6.0,
                action_items=["Simplify AI/tech concepts for non-engineers"],
                confidence=0.7,
            ))
        return opps

    def _timing_opportunities(self, competitors: List[CompetitorProfile]) -> List[Opportunity]:
        """Find timing-based opportunities."""
        opps = []
        for comp in competitors:
            if comp.best_post_times:
                hours = []
                for t in comp.best_post_times:
                    try:
                        hours.append(int(t.split(":")[0]))
                    except (ValueError, IndexError):
                        continue
                if hours and len(hours) < 3:
                    opps.append(Opportunity(
                        opp_type="timing",
                        description=f"Post during off-peak hours when '{comp.page_name}' is inactive",
                        priority="medium",
                        effort_level="low",
                        impact_score=5.5,
                        source_competitors=[comp.page_name],
                        action_items=["Test posting during competitor dead zones"],
                        confidence=0.6,
                    ))
        return opps

    def _gap_to_opportunity(self, gaps: List[ContentGap]) -> List[Opportunity]:
        """Convert detected gaps into opportunities."""
        opps = []
        priority_map = {"critical": "critical", "high": "high", "medium": "medium", "low": "low"}
        for gap in gaps:
            opps.append(Opportunity(
                opp_type=gap.gap_type,
                description=gap.description,
                priority=priority_map.get(gap.severity, "medium"),
                effort_level="medium",
                impact_score=gap.opportunity_score,
                action_items=[gap.evidence],
                confidence=0.65,
            ))
        return opps

    def _priority_weight(self, priority: str) -> int:
        return {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(priority, 0)

    def get_top_opportunities(self, count: int = 10) -> List[Opportunity]:
        """Get highest impact opportunities."""
        all_opps = []
        for opps in self._opportunities.values():
            all_opps.extend(opps)
        all_opps.sort(key=lambda o: o.impact_score, reverse=True)
        return all_opps[:count]

    def store_opportunities(self, competitor_id: str, opportunities: List[Opportunity]):
        """Store opportunities for a competitor."""
        self._opportunities[competitor_id] = opportunities
