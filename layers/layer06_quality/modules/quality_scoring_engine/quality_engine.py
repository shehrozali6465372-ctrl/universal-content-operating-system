"""Quality Engine — unified Layer 06 quality scoring and decision pipeline."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from layers.layer06_quality.modules.quality_scoring_engine.score_aggregator import ScoreAggregator
from layers.layer06_quality.modules.quality_scoring_engine.confidence_fusion import ConfidenceFusion
from layers.layer06_quality.modules.quality_scoring_engine.quality_grader import QualityGrader
from layers.layer06_quality.modules.quality_scoring_engine.decision_engine import DecisionEngine
from layers.layer06_quality.modules.quality_scoring_engine.explainability_engine import ExplainabilityEngine
from layers.layer06_quality.modules.quality_scoring_engine.risk_analyzer import RiskAnalyzer
from layers.layer06_quality.modules.quality_scoring_engine.quality_result import QualityResult, ModuleScore


REQUIRED_MODULES = frozenset({
    "content_quality",
    "fact_validation",
    "safety",
    "originality",
    "seo",
    "platform_compliance",
    "brand_voice",
})


class QualityEngine:
    """Orchestrate scoring only when the mandatory quality evidence exists."""

    def __init__(
        self,
        aggregator: Optional[ScoreAggregator] = None,
        fusion: Optional[ConfidenceFusion] = None,
        grader: Optional[QualityGrader] = None,
        decision_engine: Optional[DecisionEngine] = None,
        explainability: Optional[ExplainabilityEngine] = None,
        risk_analyzer: Optional[RiskAnalyzer] = None,
    ) -> None:
        self.aggregator = aggregator or ScoreAggregator()
        self.fusion = fusion or ConfidenceFusion()
        self.grader = grader or QualityGrader()
        self.decision_engine = decision_engine or DecisionEngine()
        self.explainability = explainability or ExplainabilityEngine()
        self.risk_analyzer = risk_analyzer or RiskAnalyzer()
        self._check_count = 0

    def score(
        self,
        module_scores: List[ModuleScore],
        layer2_confidence: float = 0.5,
        layer3_confidence: float = 0.5,
    ) -> QualityResult:
        """Score a complete result; missing required evidence rejects."""
        if not 0.0 <= layer2_confidence <= 1.0:
            raise ValueError("layer2_confidence must be between 0 and 1")
        if not 0.0 <= layer3_confidence <= 1.0:
            raise ValueError("layer3_confidence must be between 0 and 1")

        result = QualityResult()
        start_time = time.monotonic()
        result.module_scores = module_scores

        reported = {score.module_name for score in module_scores}
        missing_required = sorted(REQUIRED_MODULES - reported)
        if missing_required:
            result.hard_stops = [
                f"missing_required_module:{name}" for name in missing_required
            ]
            result.decision = "reject"
            result.risk_level = "critical"
            result.grade = "F"
            result.statistics = {
                "modules_scored": len(module_scores),
                "modules_missing": missing_required,
                "hard_stops": len(result.hard_stops),
            }
            self._check_count += 1
            return result

        result.overall_score = self.aggregator.aggregate(module_scores)
        result.confidence = self.fusion.fuse_with_context(
            module_scores, layer2_confidence, layer3_confidence,
        )
        result.grade = self.grader.grade(result.overall_score)

        risk = self.risk_analyzer.analyze(module_scores, result.overall_score)
        result.risk_level = risk.level

        decision = self.decision_engine.decide(
            result.overall_score, module_scores, result.confidence,
        )
        result.decision = decision.decision
        result.hard_stops = decision.hard_stops_triggered

        result.explanations = self.explainability.explain(
            result.overall_score,
            module_scores,
            result.decision,
            result.risk_level,
        )

        missing = self.aggregator.get_missing_modules(module_scores)
        result.statistics = {
            "scoring_time_ms": round(
                (time.monotonic() - start_time) * 1000, 2
            ),
            "modules_scored": len(module_scores),
            "modules_missing": missing,
            "hard_stops": len(result.hard_stops),
            "explanation_count": len(result.explanations),
        }
        self._check_count += 1
        return result

    def score_quick(self, module_scores: List[ModuleScore]) -> Dict[str, Any]:
        """Score and return a compact summary."""
        result = self.score(module_scores)
        return {
            "overall_score": result.overall_score,
            "grade": result.grade,
            "decision": result.decision,
            "confidence": result.confidence,
            "risk_level": result.risk_level,
        }

    def format_summary(self, result: QualityResult) -> str:
        """Format a human-readable summary."""
        return self.explainability.format_summary(
            result.overall_score,
            result.grade,
            result.decision,
            result.explanations,
        )

    @property
    def check_count(self) -> int:
        return self._check_count
