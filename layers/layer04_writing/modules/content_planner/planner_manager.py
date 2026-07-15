"""Planner Manager — Central orchestrator for Content Planner."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer04_writing.modules.content_planner.writing_plan import WritingPlan
from layers.layer04_writing.modules.content_planner.goal_analyzer import GoalAnalyzer, GoalAnalysis
from layers.layer04_writing.modules.content_planner.audience_analyzer import AudienceAnalyzer, AudienceAnalysis
from layers.layer04_writing.modules.content_planner.platform_planner import PlatformPlanner, PlatformConstraints
from layers.layer04_writing.modules.content_planner.tone_selector import ToneSelector, ToneSelection
from layers.layer04_writing.modules.content_planner.content_structure import ContentStructure, ContentStructureBuilder
from layers.layer04_writing.modules.content_planner.constraint_manager import ConstraintManager
from layers.layer04_writing.modules.content_planner.plan_validator import PlanValidator, ValidationResult


class PlannerResult:
    """Result from the Content Planner pipeline."""
    __slots__ = ("plan", "goal_analysis", "audience_analysis", "tone_selection",
                 "structure", "constraints", "validation", "metadata", "timestamp",
                 "pipeline_time_ms", "planning_id")

    def __init__(self) -> None:
        self.plan: Optional[WritingPlan] = None
        self.goal_analysis: Optional[GoalAnalysis] = None
        self.audience_analysis: Optional[AudienceAnalysis] = None
        self.tone_selection: Optional[ToneSelection] = None
        self.structure: Optional[ContentStructure] = None
        self.constraints: Optional[PlatformConstraints] = None
        self.validation: Optional[ValidationResult] = None
        self.metadata: Dict[str, Any] = {}
        self.timestamp = time.time()
        self.pipeline_time_ms = 0.0
        self.planning_id = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "planning_id": self.planning_id,
            "plan": self.plan.to_dict() if self.plan else None,
            "goal": self.goal_analysis.to_dict() if self.goal_analysis else None,
            "audience": self.audience_analysis.to_dict() if self.audience_analysis else None,
            "tone": self.tone_selection.to_dict() if self.tone_selection else None,
            "structure": self.structure.to_dict() if self.structure else None,
            "constraints": self.constraints.to_dict() if self.constraints else None,
            "validation": self.validation.to_dict() if self.validation else None,
            "pipeline_time_ms": round(self.pipeline_time_ms, 2),
            "timestamp": self.timestamp,
        }


class PlannerManager:
    """Central orchestrator for Content Planner.

    Takes inputs from Layers 1-3 (Research, Intelligence)
    and produces a complete WritingPlan ready for Draft Generator.

    Pipeline:
    Goal Analysis → Audience Analysis → Platform Planning
    → Tone Selection → Structure → Validation → WritingPlan
    """

    def __init__(
        self,
        goal_analyzer: Optional[GoalAnalyzer] = None,
        audience_analyzer: Optional[AudienceAnalyzer] = None,
        platform_planner: Optional[PlatformPlanner] = None,
        tone_selector: Optional[ToneSelector] = None,
        structure_builder: Optional[ContentStructureBuilder] = None,
        constraint_manager: Optional[ConstraintManager] = None,
        validator: Optional[PlanValidator] = None,
    ) -> None:
        self.goal_analyzer = goal_analyzer or GoalAnalyzer()
        self.audience_analyzer = audience_analyzer or AudienceAnalyzer()
        self.platform_planner = platform_planner or PlatformPlanner()
        self.tone_selector = tone_selector or ToneSelector()
        self.structure_builder = structure_builder or ContentStructureBuilder()
        self.constraint_manager = constraint_manager or ConstraintManager()
        self.validator = validator or PlanValidator()
        self._plan_count = 0

    def create_plan(
        self,
        topic: str,
        intelligence_data: Optional[Dict[str, Any]] = None,
        user_goal: Optional[str] = None,
        platform: str = "facebook",
        audience_hint: Optional[str] = None,
        tone_override: Optional[str] = None,
    ) -> PlannerResult:
        """Create a complete writing plan from intelligence inputs."""
        start = time.time()
        result = PlannerResult()
        result.planning_id = f"planner_{int(time.time() * 1000) % 10000000}"

        # 1. Goal Analysis
        result.goal_analysis = self.goal_analyzer.analyze(
            topic=topic, intelligence_data=intelligence_data, user_goal=user_goal
        )

        # 2. Audience Analysis
        result.audience_analysis = self.audience_analyzer.analyze(
            topic=topic, audience_hint=audience_hint, intel_data=intelligence_data
        )

        # 3. Platform Planning
        result.constraints = self.platform_planner.get_constraints(platform)

        # 4. Tone Selection
        result.tone_selection = self.tone_selector.select(
            goal=result.goal_analysis.primary_goal,
            audience=result.audience_analysis.audience_type,
            platform=platform,
            override=tone_override,
        )

        # 5. Content Structure
        result.structure = self.structure_builder.build(
            goal=result.goal_analysis.primary_goal,
            content_type="post",
        )

        # 6. Build WritingPlan
        plan = WritingPlan(topic=topic)
        plan.goal = result.goal_analysis.primary_goal
        plan.platform = platform
        plan.audience = result.audience_analysis.audience_type
        plan.tone = result.tone_selection.selected_tone
        plan.length = result.audience_analysis.recommended_length
        plan.emoji_level = result.audience_analysis.recommended_emoji_level
        plan.cta = result.goal_analysis.suggested_cta
        plan.structure = result.structure.to_dict()

        # Apply platform constraints
        if result.constraints:
            plan.constraints = {
                "max_length": result.constraints.max_length,
                "recommended_hashtags": result.constraints.recommended_hashtags,
                "best_practices": result.constraints.best_practices,
            }

        # 7. Validation
        result.validation = self.validator.validate(plan)
        if not result.validation.is_valid:
            # Create a minimal valid plan as fallback
            errors = result.validation.errors
            result.metadata["validation_warnings"] = errors

        result.plan = plan
        result.pipeline_time_ms = (time.time() - start) * 1000
        self._plan_count += 1
        return result

    def update_plan(self, plan: WritingPlan, updates: Dict[str, Any]) -> PlannerResult:
        """Update an existing plan and re-validate."""
        for field, value in updates.items():
            if hasattr(plan, field):
                setattr(plan, field, value)
        plan.updated_at = time.time()
        plan.version += 1

        validation = self.validator.validate(plan)
        result = PlannerResult()
        result.plan = plan
        result.validation = validation
        result.metadata = {"updated": True}
        return result

    def validate_plan(self, plan: WritingPlan) -> ValidationResult:
        """Validate a writing plan."""
        return self.validator.validate(plan)

    def export_plan(self, plan: WritingPlan) -> Dict[str, Any]:
        """Export a plan as dictionary."""
        return plan.to_dict()

    def import_plan(self, data: Dict[str, Any]) -> WritingPlan:
        """Import a plan from dictionary."""
        return WritingPlan.from_dict(data)

    def get_history(self) -> List[Dict[str, Any]]:
        """Get planning history."""
        return []

    @property
    def plan_count(self) -> int:
        return self._plan_count
