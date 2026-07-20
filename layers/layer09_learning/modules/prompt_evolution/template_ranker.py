"""TemplateRanker — Ranks templates by real-world performance from database.

Connects PerformanceTracker to DatabaseManager so that:
1. Published content performance is tracked
2. Templates are ranked by actual engagement
3. Best templates are automatically selected for future content

Architecture:
    Published Content → Analytics → PerformanceTracker → TemplateRanker → Best Template
"""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
from layers.layer09_learning.modules.prompt_evolution.performance_tracker import PerformanceTracker
from layers.layer09_learning.modules.prompt_evolution.template_memory import TemplateMemory


class TemplateRanker:
    """Ranks templates by real-world performance data.

    Integrates with:
    - DatabaseManager (reads published_posts + analytics_cache)
    - PerformanceTracker (records events)
    - TemplateMemory (stores/ranks templates)
    """

    def __init__(self, memory: Optional[TemplateMemory] = None,
                 tracker: Optional[PerformanceTracker] = None) -> None:
        self._memory = memory or TemplateMemory()
        self._tracker = tracker or PerformanceTracker()
        self._rankings: Dict[str, float] = {}

    def rank_template(self, template: PromptTemplate,
                      impressions: int = 0, engagements: int = 0,
                      clicks: int = 0) -> float:
        """Rank a template based on performance data.

        Returns a score from 0.0 to 10.0.
        """
        # Record event in tracker
        self._tracker.record_event(
            template.template_id, template.platform,
            impressions, engagements, clicks,
        )
        # Update template metrics
        self._tracker.update_template_from_events(template)
        # Store updated ranking
        self._rankings[template.template_id] = template.score
        return template.score

    def rank_batch(self, templates: List[PromptTemplate],
                   performance_data: List[Dict[str, int]]) -> List[Dict[str, Any]]:
        """Rank multiple templates with their performance data.

        Args:
            templates: List of PromptTemplate objects
            performance_data: List of dicts with impressions, engagements, clicks

        Returns:
            Sorted list of ranking results
        """
        results = []
        for tpl, perf in zip(templates, performance_data):
            score = self.rank_template(
                tpl,
                impressions=perf.get("impressions", 0),
                engagements=perf.get("engagements", 0),
                clicks=perf.get("clicks", 0),
            )
            results.append({
                "template_id": tpl.template_id,
                "score": round(score, 2),
                "engagement_rate": round(tpl.engagement_rate, 4),
                "click_rate": round(tpl.click_rate, 4),
                "total_uses": tpl.total_uses,
                "is_champion": tpl.is_champion,
                "is_challenger": tpl.is_challenger,
                "platform": tpl.platform,
                "hook_type": tpl.hook_type,
                "cta_type": tpl.cta_type,
            })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def get_best_template(self, platform: str = "facebook",
                         topic: str = "") -> Optional[PromptTemplate]:
        """Get the highest-ranked template for a platform/topic."""
        candidates = self._memory.search(
            platform=platform, topic=topic if topic else None,
            limit=50,
        )
        if not candidates:
            return None

        # Sort by score
        candidates.sort(key=lambda t: t.score, reverse=True)
        return candidates[0]

    def get_rankings(self, platform: Optional[str] = None,
                    limit: int = 20) -> List[Dict[str, Any]]:
        """Get current rankings for all templates."""
        templates = self._memory.search(platform=platform, limit=limit)
        rankings = []
        for tpl in templates:
            rankings.append({
                "template_id": tpl.template_id,
                "score": round(tpl.score, 2),
                "platform": tpl.platform,
                "hook_type": tpl.hook_type,
                "cta_type": tpl.cta_type,
                "total_uses": tpl.total_uses,
                "engagement_rate": round(tpl.engagement_rate, 4),
                "is_champion": tpl.is_champion,
                "is_challenger": tpl.is_challenger,
                "is_retired": tpl.is_retired,
            })
        rankings.sort(key=lambda x: x["score"], reverse=True)
        return rankings

    def get_hook_performance(self, platform: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Get performance breakdown by hook type."""
        templates = self._memory.search(platform=platform, limit=200)
        hook_stats: Dict[str, Dict[str, Any]] = {}

        for tpl in templates:
            hook = tpl.hook_type
            if hook not in hook_stats:
                hook_stats[hook] = {
                    "count": 0, "total_score": 0.0,
                    "avg_score": 0.0, "best_score": 0.0,
                }
            hook_stats[hook]["count"] += 1
            hook_stats[hook]["total_score"] += tpl.score
            hook_stats[hook]["best_score"] = max(hook_stats[hook]["best_score"], tpl.score)

        for hook in hook_stats:
            count = hook_stats[hook]["count"]
            hook_stats[hook]["avg_score"] = round(
                hook_stats[hook]["total_score"] / max(count, 1), 2
            )

        return hook_stats

    def get_cta_performance(self, platform: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Get performance breakdown by CTA type."""
        templates = self._memory.search(platform=platform, limit=200)
        cta_stats: Dict[str, Dict[str, Any]] = {}

        for tpl in templates:
            cta = tpl.cta_type
            if cta not in cta_stats:
                cta_stats[cta] = {
                    "count": 0, "total_score": 0.0,
                    "avg_score": 0.0, "best_score": 0.0,
                }
            cta_stats[cta]["count"] += 1
            cta_stats[cta]["total_score"] += tpl.score
            cta_stats[cta]["best_score"] = max(cta_stats[cta]["best_score"], tpl.score)

        for cta in cta_stats:
            count = cta_stats[cta]["count"]
            cta_stats[cta]["avg_score"] = round(
                cta_stats[cta]["total_score"] / max(count, 1), 2
            )

        return cta_stats

    def get_memory(self) -> TemplateMemory:
        return self._memory

    def get_tracker(self) -> PerformanceTracker:
        return self._tracker
