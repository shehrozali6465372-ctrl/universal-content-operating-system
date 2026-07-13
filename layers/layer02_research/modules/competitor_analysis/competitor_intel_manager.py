"""
Competitor Intelligence Manager
Layer 2: Research Engine — Module 3

Central manager that orchestrates all competitor analysis:
- Competitor CRUD
- Profile management
- Full analysis pipeline
- Gap detection
- Opportunity discovery
- Persistent storage
- Health check
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional

from layers.layer02_research.modules.competitor_analysis.competitor_profile import CompetitorProfile
from layers.layer02_research.modules.competitor_analysis.content_analyzer import ContentAnalyzer, ContentPost
from layers.layer02_research.modules.competitor_analysis.posting_pattern_analyzer import PostingPatternAnalyzer
from layers.layer02_research.modules.competitor_analysis.engagement_analyzer import EngagementAnalyzer
from layers.layer02_research.modules.competitor_analysis.writing_style_analyzer import WritingStyleAnalyzer
from layers.layer02_research.modules.competitor_analysis.gap_detector import GapDetector, ContentGap
from layers.layer02_research.modules.competitor_analysis.opportunity_finder import OpportunityFinder, Opportunity
from layers.layer02_research.modules.competitor_analysis.exceptions import (
    CompetitorNotFoundError,
    DuplicateCompetitorError,
)


class CompetitorIntelManager:
    """Central competitor intelligence engine."""

    def __init__(self, storage_path: Optional[str] = None):
        self._competitors: Dict[str, CompetitorProfile] = {}
        self._lock = Lock()
        self._storage_path = Path(storage_path) if storage_path else None

        # Sub-analyzers
        self.content_analyzer = ContentAnalyzer()
        self.posting_analyzer = PostingPatternAnalyzer()
        self.engagement_analyzer = EngagementAnalyzer()
        self.writing_analyzer = WritingStyleAnalyzer()
        self.gap_detector = GapDetector()
        self.opportunity_finder = OpportunityFinder()

        # Results
        self._gaps: List[ContentGap] = []
        self._opportunities: List[Opportunity] = []
        self._history: List[dict] = []
        self._max_history = 500

        self._load()

    # ── CRUD ────────────────────────────────

    def add_competitor(
        self,
        page_name: str,
        page_url: str = "",
        niche: str = "general",
        category: str = "general",
        followers: int = 0,
        following: int = 0,
        post_count: int = 0,
        posting_frequency: str = "unknown",
        avg_posts_per_day: float = 0.0,
        top_topics: Optional[List[str]] = None,
        top_hashtags: Optional[List[str]] = None,
        top_formats: Optional[List[str]] = None,
        writing_style: str = "unknown",
        tone: str = "neutral",
        image_style: str = "unknown",
        avg_engagement_rate: float = 0.0,
        avg_likes: float = 0.0,
        avg_comments: float = 0.0,
        avg_shares: float = 0.0,
        engagement_trend: str = "unknown",
        growth_score: float = 0.0,
        confidence: float = 0.5,
        tags: Optional[List[str]] = None,
    ) -> CompetitorProfile:
        """Add a new competitor."""
        with self._lock:
            for comp in self._competitors.values():
                if comp.page_name.lower() == page_name.lower():
                    raise DuplicateCompetitorError(f"Competitor '{page_name}' already exists")

        profile = CompetitorProfile(
            page_name=page_name, page_url=page_url, niche=niche, category=category,
            followers=followers, following=following, post_count=post_count,
            posting_frequency=posting_frequency, avg_posts_per_day=avg_posts_per_day,
            top_topics=top_topics or [], top_hashtags=top_hashtags or [], top_formats=top_formats or [],
            writing_style=writing_style, tone=tone, image_style=image_style,
            avg_engagement_rate=avg_engagement_rate,
            avg_likes=avg_likes, avg_comments=avg_comments, avg_shares=avg_shares,
            engagement_trend=engagement_trend, growth_score=growth_score,
            confidence=confidence, tags=tags,
        )

        with self._lock:
            self._competitors[profile.competitor_id] = profile
            self._record_event("competitor_added", profile.competitor_id, {"name": page_name})
            self._save()

        return profile

    def get_competitor(self, competitor_id: str) -> CompetitorProfile:
        with self._lock:
            comp = self._competitors.get(competitor_id)
        if comp is None:
            raise CompetitorNotFoundError(f"Competitor '{competitor_id}' not found")
        return comp

    def get_by_name(self, name: str) -> Optional[CompetitorProfile]:
        with self._lock:
            for comp in self._competitors.values():
                if comp.page_name.lower() == name.lower():
                    return comp
        return None

    def update_competitor(self, competitor_id: str, **kwargs) -> CompetitorProfile:
        with self._lock:
            comp = self._competitors.get(competitor_id)
            if comp is None:
                raise CompetitorNotFoundError(f"Competitor '{competitor_id}' not found")
            for key, val in kwargs.items():
                if hasattr(comp, key):
                    setattr(comp, key, val)
            comp.updated_at = datetime.now(timezone.utc).isoformat()
            self._record_event("competitor_updated", competitor_id, {"fields": list(kwargs.keys())})
            self._save()
        return comp

    def delete_competitor(self, competitor_id: str) -> bool:
        with self._lock:
            if competitor_id not in self._competitors:
                raise CompetitorNotFoundError(f"Competitor '{competitor_id}' not found")
            del self._competitors[competitor_id]
            self._record_event("competitor_deleted", competitor_id, {})
            self._save()
        return True

    def list_competitors(self, niche: Optional[str] = None, status: Optional[str] = None) -> List[CompetitorProfile]:
        with self._lock:
            comps = list(self._competitors.values())
        if niche:
            comps = [c for c in comps if c.niche == niche]
        if status:
            comps = [c for c in comps if c.status == status]
        return comps

    def exists(self, name: str) -> bool:
        with self._lock:
            return any(c.page_name.lower() == name.lower() for c in self._competitors.values())

    # ── Analysis ────────────────────────────

    def add_posts(self, competitor_id: str, posts: List[ContentPost]):
        """Add posts for content analysis."""
        self.get_competitor(competitor_id)  # Validates existence
        self.content_analyzer.add_posts(competitor_id, posts)

    def run_full_analysis(self, competitor_id: str) -> CompetitorProfile:
        """Run complete analysis pipeline on a competitor."""
        comp = self.get_competitor(competitor_id)
        posts = self.content_analyzer.get_posts(competitor_id)

        # Content analysis
        if posts:
            self.content_analyzer.update_profile_from_posts(comp)

        # Posting patterns
        pattern = self.posting_analyzer.analyze(competitor_id, posts)
        comp.posting_frequency = pattern.posting_frequency
        comp.avg_posts_per_day = pattern.avg_posts_per_day
        comp.best_post_times = [f"{h:02d}:00" for h in pattern.best_hours]

        # Engagement analysis
        metrics = self.engagement_analyzer.analyze(competitor_id, posts)
        comp.avg_engagement_rate = metrics.avg_engagement_rate
        comp.engagement_trend = metrics.engagement_trend
        comp.strengths = self.engagement_analyzer.get_strengths(competitor_id)
        comp.weaknesses = self.engagement_analyzer.get_weaknesses(competitor_id)

        # Writing style
        texts = [p.text for p in posts if p.text]
        hashtags_per_post = [p.hashtags for p in posts]
        if texts:
            self.writing_analyzer.analyze(competitor_id, texts, hashtags_per_post)

        # Opportunity score
        comp.calculate_opportunity_score()
        comp.last_analyzed = datetime.now(timezone.utc).isoformat()
        comp.updated_at = comp.last_analyzed

        with self._lock:
            self._save()

        return comp

    def detect_gaps(self, known_topics: Optional[List[str]] = None) -> List[ContentGap]:
        """Detect content gaps across all competitors."""
        with self._lock:
            competitors = list(self._competitors.values())
        self._gaps = self.gap_detector.detect_all(competitors, known_topics or [])
        return self._gaps

    def find_opportunities(self) -> List[Opportunity]:
        """Find opportunities across all competitors."""
        with self._lock:
            competitors = list(self._competitors.values())
        self._opportunities = self.opportunity_finder.discover_all(
            competitors,
            engagement_analyzer=self.engagement_analyzer,
            writing_analyzer=self.writing_analyzer,
            gaps=self._gaps,
        )
        return self._opportunities

    def compare_two(self, comp_id_a: str, comp_id_b: str) -> Dict:
        """Compare two competitors."""
        a = self.get_competitor(comp_id_a)
        b = self.get_competitor(comp_id_b)

        comparison = {
            "competitor_a": a.page_name,
            "competitor_b": b.page_name,
            "followers_diff": a.followers - b.followers,
            "engagement_rate_diff": a.avg_engagement_rate - b.avg_engagement_rate,
            "growth_score_diff": a.growth_score - b.growth_score,
            "opportunity_score_diff": a.opportunity_score - b.opportunity_score,
            "a_strengths": a.strengths,
            "a_weaknesses": a.weaknesses,
            "b_strengths": b.strengths,
            "b_weaknesses": b.weaknesses,
        }

        # Engagement comparison
        eng_compare = self.engagement_analyzer.compare_engagement(comp_id_a, comp_id_b)
        if "error" not in eng_compare:
            comparison["engagement"] = eng_compare

        # Posting pattern comparison
        pattern_compare = self.posting_analyzer.compare_patterns(comp_id_a, comp_id_b)
        if "error" not in pattern_compare:
            comparison["posting_patterns"] = pattern_compare

        # Writing style comparison
        ws_a = self.writing_analyzer.get_profile(comp_id_a)
        ws_b = self.writing_analyzer.get_profile(comp_id_b)
        if ws_a and ws_b:
            comparison["writing_style"] = {
                "a_tone": ws_a.tone,
                "b_tone": ws_b.tone,
                "a_avg_words": ws_a.avg_word_count,
                "b_avg_words": ws_b.avg_word_count,
                "differentiation": self.writing_analyzer.detect_differentiation(ws_a, ws_b),
            }

        return comparison

    def get_leaderboard(self) -> List[Dict]:
        """Get ranked leaderboard of competitors."""
        with self._lock:
            competitors = list(self._competitors.values())
        competitors.sort(key=lambda c: c.opportunity_score, reverse=True)
        return [
            {
                "rank": i + 1,
                "name": c.page_name,
                "niche": c.niche,
                "followers": c.followers,
                "engagement_rate": c.avg_engagement_rate,
                "opportunity_score": c.opportunity_score,
                "strengths": len(c.strengths),
                "weaknesses": len(c.weaknesses),
            }
            for i, c in enumerate(competitors)
        ]

    def health_check(self) -> dict:
        with self._lock:
            comps = list(self._competitors.values())
        active = sum(1 for c in comps if c.status == "active")
        analyzed = sum(1 for c in comps if c.data_quality == "analyzed")
        return {
            "total_competitors": len(comps),
            "active": active,
            "analyzed": analyzed,
            "gaps_detected": len(self._gaps),
            "opportunities_found": len(self._opportunities),
            "content_analyzer_ready": True,
            "posting_analyzer_ready": True,
            "engagement_analyzer_ready": True,
            "writing_analyzer_ready": True,
        }

    # ── Storage ─────────────────────────────

    def _record_event(self, event_type: str, comp_id: str, data: dict):
        entry = {
            "event": event_type,
            "competitor_id": comp_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data,
        }
        self._history.append(entry)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def _save(self):
        if self._storage_path is None:
            return
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "competitors": [c.to_dict() for c in self._competitors.values()],
            "history": self._history[-50:],
        }
        self._storage_path.write_text(json.dumps(data, indent=2))

    def _load(self):
        if self._storage_path is None or not self._storage_path.exists():
            return
        try:
            data = json.loads(self._storage_path.read_text())
            for cd in data.get("competitors", []):
                comp = CompetitorProfile.from_dict(cd)
                self._competitors[comp.competitor_id] = comp
            self._history = data.get("history", [])
        except (json.JSONDecodeError, KeyError):
            pass
