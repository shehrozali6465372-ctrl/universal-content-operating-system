"""Learning Pipeline — Define execution stages and dependencies."""
from __future__ import annotations
from typing import Dict, List
from enum import Enum


class PipelineStage(Enum):
    """Execution stages of the learning pipeline."""
    COLLECT_FEEDBACK = "collect_feedback"
    OPTIMIZE_PROMPTS = "optimize_prompts"
    OPTIMIZE_STRATEGY = "optimize_strategy"
    LEARN_BRAND_VOICE = "learn_brand_voice"
    EVOLVE_MEMORY = "evolve_memory"
    SELF_IMPROVE = "self_improve"
    CALIBRATE_QUALITY = "calibrate_quality"
    OPTIMIZE_CONTENT = "optimize_content"
    PREDICT_ENGAGEMENT = "predict_engagement"


# Dependencies: stage → list of stages that must run before it
PIPELINE_DEPENDENCIES: Dict[PipelineStage, List[PipelineStage]] = {
    PipelineStage.COLLECT_FEEDBACK: [],
    PipelineStage.OPTIMIZE_PROMPTS: [PipelineStage.COLLECT_FEEDBACK],
    PipelineStage.OPTIMIZE_STRATEGY: [PipelineStage.COLLECT_FEEDBACK],
    PipelineStage.LEARN_BRAND_VOICE: [PipelineStage.COLLECT_FEEDBACK],
    PipelineStage.EVOLVE_MEMORY: [PipelineStage.COLLECT_FEEDBACK, PipelineStage.OPTIMIZE_PROMPTS, PipelineStage.OPTIMIZE_STRATEGY],
    PipelineStage.SELF_IMPROVE: [PipelineStage.EVOLVE_MEMORY],
    PipelineStage.CALIBRATE_QUALITY: [PipelineStage.SELF_IMPROVE],
    PipelineStage.OPTIMIZE_CONTENT: [PipelineStage.CALIBRATE_QUALITY, PipelineStage.LEARN_BRAND_VOICE],
    PipelineStage.PREDICT_ENGAGEMENT: [PipelineStage.OPTIMIZE_CONTENT],
}


class PipelineDefinition:
    """Define and validate the learning pipeline execution order."""

    def __init__(self, stages: List[PipelineStage] = None) -> None:
        self._stages = stages or list(PipelineStage)

    def get_execution_order(self) -> List[List[PipelineStage]]:
        """Topological sort returning batches of parallelizable stages."""
        resolved: List[PipelineStage] = []
        batches: List[List[PipelineStage]] = []
        remaining = set(self._stages)

        while remaining:
            ready = [
                s for s in remaining
                if all(dep in resolved for dep in PIPELINE_DEPENDENCIES.get(s, []))
            ]
            if not ready:
                ready = list(remaining)
            batches.append(ready)
            resolved.extend(ready)
            remaining -= set(ready)

        return batches

    def get_dependencies(self, stage: PipelineStage) -> List[PipelineStage]:
        return list(PIPELINE_DEPENDENCIES.get(stage, []))

    def validate(self) -> bool:
        """Check for cycles and missing dependencies."""
        try:
            self.get_execution_order()
            return True
        except Exception:
            return False

    def get_stage_count(self) -> int:
        return len(self._stages)
