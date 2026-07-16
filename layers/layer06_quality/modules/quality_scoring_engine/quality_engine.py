"""Quality Engine — Core orchestrator for quality scoring pipeline.

Fuses all module scores into a unified QualityResult with
decision, grade, risk, and explainability.
"""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer06_quality.modules.quality_scoring_engine.score_aggregator import ScoreAggregator
from layers.layer06_quality.modules.quality_scoring_engine.confidence_fusion import ConfidenceFusion
from layers.layer06_quality.modules.quality_scoring_engine.quality_grader import QualityGrader
from layers.layer06_quality.modules.quality_scoring_engine.decision_engine import DecisionEngine
from layers.layer06_quality.modules.quality_scoring_engine.explainability_engine import ExplainabilityEngine
from layers.layer06_quality.modules.quality_scoring_engine.risk_analyzer import RiskAnalyzer
from layers.layer06_quality.modules.quality_scoring_engine.quality_result import (
    QualityResult, ModuleScore,
)


class QualityEngine:
    """Orchestrates full quality scoring and decision pipeline."""

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
        """Full quality scoring pipeline."""
        result = QualityResult()
        start_time = time.time()

        # Store module scores
        result.module_scores = module_scores

        # 1. Aggregate scores
        result.overall_score = self.aggregator.aggregate(module_scores)

        # 2. Fuse confidence
        result.confidence = self.fusion.fuse_with_context(
            module_scores, layer2_confidence, layer3_confidence,
        )

        # 3. Grade
        result.grade = self.grader.grade(result.overall_score)

        # 4. Risk analysis
        risk = self.risk_analyzer.analyze(module_scores, result.overall_score)
        result.risk_level = risk.level

        # 5. Decision
        decision = self.decision_engine.decide(
            result.overall_score, module_scores, result.confidence,
        )
        result.decision = decision.decision
        result.hard_stops = decision.hard_stops_triggered

        # 6. Explanations
        result.explanations = self.explainability.explain(
            result.overall_score, module_scores,
            result.decision, result.risk_level,
        )

        # 7. Statistics
        elapsed = time.time() - start_time
        missing = self.aggregator.get_missing_modules(module_scores)
        result.statistics = {
            "scoring_time_ms": round(elapsed * 1000, 2),
            "modules_scored": len(module_scores),
            "modules_missing": missing,
            "hard_stops": len(result.hard_stops),
            "explanation_count": len(result.explanations),
        }

        self._check_count += 1
        return result

    def score_quick(self, module_scores: List[ModuleScore]) -> Dict[str, Any]:
        """Quick scoring returning summary."""
        result = self.score(module_scores)
        return {
            "overall_score": result.overall_score,
            "grade": result.grade,
            "decision": result.decision,
            "confidence": result.confidence,
            "risk_level": result.risk_level,
        }

    def format_summary(self, result: QualityResult) -> str:
        """Format human-readable summary."""
        return self.explainability.format_summary(
            result.overall_score, result.grade,
            result.decision, result.explanations,
        )

    @property
    def check_count(self) -> int:
        return self._check_count
