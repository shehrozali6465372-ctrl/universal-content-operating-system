"""EvolutionEngine — The self-improving brain of prompt optimization.

Orchestrates the full evolution cycle:
1. Analyze performance data
2. Identify winning patterns
3. Retire underperformers
4. Generate new variations from winners
5. A/B test new variants
6. Promote champions

Usage:
    engine = EvolutionEngine()
    # After content is published and metrics come in:
    engine.evolve(topic="AI", platform="facebook")
    # Get the best template for next time:
    best = engine.get_best_template("AI", "facebook")
"""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate
from layers.layer09_learning.modules.prompt_evolution.style_library import StyleLibrary
from layers.layer09_learning.modules.prompt_evolution.template_memory import TemplateMemory
from layers.layer09_learning.modules.prompt_evolution.performance_tracker import PerformanceTracker
from layers.layer09_learning.modules.prompt_evolution.variation_engine import VariationEngine


class EvolutionCycle:
    """Result of a single evolution cycle."""

    __slots__ = ("cycle_id", "topic", "platform", "templates_analyzed",
                 "champions_found", "challengers_generated",
                 "retired", "promoted", "duration_ms", "insights")

    def __init__(self) -> None:
        self.cycle_id: str = f"evo_{int(time.time() * 1000)}"
        self.topic: str = ""
        self.platform: str = ""
        self.templates_analyzed: int = 0
        self.champions_found: int = 0
        self.challengers_generated: int = 0
        self.retired: int = 0
        self.promoted: int = 0
        self.duration_ms: float = 0.0
        self.insights: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id, "topic": self.topic,
            "platform": self.platform,
            "templates_analyzed": self.templates_analyzed,
            "champions_found": self.champions_found,
            "challengers_generated": self.challengers_generated,
            "retired": self.retired, "promoted": self.promoted,
            "duration_ms": round(self.duration_ms, 1),
            "insights": self.insights,
        }


class EvolutionEngine:
    """Self-improving prompt evolution engine.

    Core loop:
    1. Fetch templates for topic/platform
    2. Update their scores from performance data
    3. Retire templates with score < 3.0 (after 10+ uses)
    4. Promote templates with score > 8.0 to champion
    5. Generate A/B test variants from champions
    6. Store new variants in memory
    """

    def __init__(
        self,
        memory: Optional[TemplateMemory] = None,
        tracker: Optional[PerformanceTracker] = None,
        variation_engine: Optional[VariationEngine] = None,
        style_library: Optional[StyleLibrary] = None,
    ) -> None:
        self._memory = memory or TemplateMemory()
        self._tracker = tracker or PerformanceTracker()
        self._variations = variation_engine or VariationEngine(style_library)
        self._styles = style_library or StyleLibrary()
        self._evolution_history: List[EvolutionCycle] = []

    def evolve(self, topic: str = "", platform: str = "facebook",
               generate_variants: bool = True) -> EvolutionCycle:
        """Run one evolution cycle."""
        start = time.time()
        cycle = EvolutionCycle()
        cycle.topic = topic
        cycle.platform = platform

        # 1. Get templates
        templates = self._memory.search(platform=platform, topic=topic, limit=100)
        cycle.templates_analyzed = len(templates)

        # 2. Update scores from performance data
        for tpl in templates:
            self._tracker.update_template_from_events(tpl)

        # 3. Find champions
        champions = [t for t in templates if t.is_champion]
        cycle.champions_found = len(champions)

        # 4. Retire underperformers
        retired = [t for t in templates if t.is_retired]
        for tpl in retired:
            self._memory.remove(tpl.template_id)
            cycle.retired += 1
            cycle.insights.append(f"Retired template {tpl.template_id} (score={tpl.score:.1f})")

        # 5. Generate challengers from champions
        if generate_variants and champions:
            for champ in champions[:3]:  # Top 3 champions
                challengers = self._variations.generate_ab_test(champ, count=2)
                for ch in challengers:
                    self._memory.store(ch)
                    cycle.challengers_generated += 1
            cycle.insights.append(f"Generated {cycle.challengers_generated} challengers from {len(champions)} champions")

        # 6. If no templates exist, seed from style library
        if not templates:
            self._seed_from_styles(topic, platform, cycle)

        cycle.duration_ms = (time.time() - start) * 1000
        self._evolution_history.append(cycle)
        return cycle

    def get_best_template(self, topic: str, platform: str = "facebook") -> Optional[PromptTemplate]:
        """Get the best template for a topic + platform."""
        templates = self._memory.get_best_for_topic(topic, platform, limit=5)
        if templates:
            return templates[0]
        # Fallback: create one from style library
        return self._create_default_template(topic, platform)

    def record_performance(
        self, template_id: str, platform: str,
        impressions: int, engagements: int, clicks: int,
    ) -> None:
        """Record real-world performance for a template."""
        self._tracker.record_post_published(
            template_id, platform, impressions, engagements, clicks,
        )
        # Update the template in memory
        tpl = self._memory.get(template_id)
        if tpl:
            self._tracker.update_template_from_events(tpl)

    def get_insights(self, platform: Optional[str] = None) -> Dict[str, Any]:
        """Get evolution insights."""
        templates = self._memory.search(platform=platform, limit=100)
        if not templates:
            return {"status": "no_data", "message": "No templates in memory"}

        scores = [t.score for t in templates]
        champions = [t for t in templates if t.is_champion]
        challengers = [t for t in templates if t.is_challenger]

        best_hooks = {}
        for t in templates:
            if t.hook_type not in best_hooks or t.score > best_hooks[t.hook_type]:
                best_hooks[t.hook_type] = t.score

        return {
            "total_templates": len(templates),
            "champions": len(champions),
            "challengers": len(challengers),
            "avg_score": round(sum(scores) / len(scores), 2),
            "best_hooks": best_hooks,
            "total_evolutions": len(self._evolution_history),
            "platforms": list(set(t.platform for t in templates)),
        }

    def get_memory(self) -> TemplateMemory:
        return self._memory

    def get_tracker(self) -> PerformanceTracker:
        return self._tracker

    def get_variation_engine(self) -> VariationEngine:
        return self._variations

    def _seed_from_styles(self, topic: str, platform: str,
                          cycle: EvolutionCycle) -> None:
        """Create initial templates from style library when memory is empty."""
        style_names = self._styles.get_platform_styles(platform)
        if not style_names:
            style_names = self._styles.list_styles()[:3]

        for style_name in style_names[:3]:
            tpl = self._variations.generate_from_style(topic, platform, style_name)
            self._memory.store(tpl)
            cycle.challengers_generated += 1

        cycle.insights.append(f"Seeded {min(3, len(style_names))} templates from style library")

    def _create_default_template(self, topic: str, platform: str) -> PromptTemplate:
        """Create a default template when no templates exist."""
        tpl = PromptTemplate(topic=topic, platform=platform)
        tpl.hook_template = f"Let's explore {topic}."
        tpl.cta_template = "What do you think?"
        tpl.body_template = "{hook}\n\n{body}\n\n{cta}"
        self._memory.store(tpl)
        return tpl
