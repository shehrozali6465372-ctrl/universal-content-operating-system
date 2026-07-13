"""
Scoring Engine
Layer 2: Research Engine — Module 8

Core scoring engine combining all components:
- Score aggregation from all modules
- Rule-based adjustments
- Opportunity and risk assessment
- Confidence fusion
- Recommendation generation
"""

from typing import Dict, List, Optional
from layers.layer02_research.modules.topic_scoring.scoring_rules import ScoringRulesEngine
from layers.layer02_research.modules.topic_scoring.weight_manager import WeightManager
from layers.layer02_research.modules.topic_scoring.score_normalizer import ScoreNormalizer
from layers.layer02_research.modules.topic_scoring.opportunity_scorer import OpportunityScorer
from layers.layer02_research.modules.topic_scoring.risk_scorer import RiskScorer
from layers.layer02_research.modules.topic_scoring.confidence_fusion import ConfidenceFusion
from layers.layer02_research.shared.confidence_engine import ConfidenceResult


class ScoringResult:
    """Complete scoring result for a topic."""

    __slots__ = (
        "topic", "niche", "raw_scores", "weighted_scores",
        "overall_score", "opportunity", "risk",
        "confidence_result", "recommendation", "confidence",
    )

    RECOMMENDATIONS = ["strong_publish", "publish", "conditional_publish", "revise", "skip"]

    def __init__(self, topic: str = "", niche: str = "general"):
        self.topic = topic
        self.niche = niche
        self.raw_scores: Dict[str, float] = {}
        self.weighted_scores: Dict[str, float] = {}
        self.overall_score = 0.0
        self.opportunity = None
        self.risk = None
        self.confidence_result = ConfidenceResult()
        self.recommendation = "skip"
        self.confidence = 0.0

    def to_dict(self) -> dict:
        return {
            "topic": self.topic, "niche": self.niche,
            "overall_score": self.overall_score,
            "raw_scores": self.raw_scores,
            "weighted_scores": self.weighted_scores,
            "opportunity": self.opportunity.to_dict() if self.opportunity else None,
            "risk": self.risk.to_dict() if self.risk else None,
            "confidence": self.confidence,
            "risk_level": self.confidence_result.risk_level,
            "recommendation": self.recommendation,
            "reasons": self.confidence_result.reasons,
            "evidence": self.confidence_result.evidence,
        }


class ScoringEngine:
    """Core scoring engine."""

    def __init__(
        self,
        weight_manager: Optional[WeightManager] = None,
        rules_engine: Optional[ScoringRulesEngine] = None,
        normalizer: Optional[ScoreNormalizer] = None,
        opportunity_scorer: Optional[OpportunityScorer] = None,
        risk_scorer: Optional[RiskScorer] = None,
        confidence_fusion: Optional[ConfidenceFusion] = None,
    ):
        self.weight_manager = weight_manager or WeightManager()
        self.rules_engine = rules_engine or ScoringRulesEngine()
        self.normalizer = normalizer or ScoreNormalizer()
        self.opportunity_scorer = opportunity_scorer or OpportunityScorer()
        self.risk_scorer = risk_scorer or RiskScorer()
        self.confidence_fusion = confidence_fusion or ConfidenceFusion()

    def score(
        self,
        topic: str,
        niche: str = "general",
        scores: Optional[Dict[str, float]] = None,
        evidence: Optional[List[str]] = None,
    ) -> ScoringResult:
        """Full scoring pipeline for a topic."""
        result = ScoringResult(topic, niche)
        scores = scores or {}

        # Normalize raw scores to 0-10
        result.raw_scores = {k: self.normalizer.clip(v) for k, v in scores.items()}

        # Get niche-specific weights
        weights = self.weight_manager.get_weights(niche)

        # Compute weighted scores
        weighted = {}
        for dim, weight in weights.items():
            raw = result.raw_scores.get(dim, 5.0)
            weighted[dim] = round(raw * weight, 3)
        result.weighted_scores = weighted

        # Base overall score (weighted average)
        base_score = self.normalizer.weighted_average(
            {k: result.raw_scores.get(k, 5.0) for k in weights},
            weights,
        )

        # Apply rules (bonuses/penalties)
        rule_bonus = self.rules_engine.compute_bonus(result.raw_scores)

        # Final overall score
        result.overall_score = round(max(0, min(10, base_score + rule_bonus)), 2)

        # Opportunity assessment
        result.opportunity = self.opportunity_scorer.calculate(
            trend_score=result.raw_scores.get("trend", 5.0),
            competition_score=result.raw_scores.get("competition", 5.0),
            audience_score=result.raw_scores.get("audience", 5.0),
            knowledge_score=result.raw_scores.get("knowledge", 5.0),
            engagement_score=result.raw_scores.get("engagement", 5.0),
        )

        # Risk assessment
        result.risk = self.risk_scorer.calculate(
            trend_score=result.raw_scores.get("trend", 5.0),
            competition_score=result.raw_scores.get("competition", 5.0),
            knowledge_score=result.raw_scores.get("knowledge", 5.0),
            audience_score=result.raw_scores.get("audience", 5.0),
            verification_score=result.raw_scores.get("verification", 5.0),
        )

        # Confidence fusion
        module_confidences = {
            k: v / 10.0 for k, v in result.raw_scores.items()
        }
        all_evidence = list(evidence or [])
        if result.risk.risk_factors:
            all_evidence.extend([f"Risk: {r}" for r in result.risk.risk_factors])
        result.confidence_result = self.confidence_fusion.fuse(module_confidences, all_evidence)
        result.confidence = result.confidence_result.confidence

        # Recommendation
        result.recommendation = self._determine_recommendation(result)

        return result

    def _determine_recommendation(self, result: ScoringResult) -> str:
        """Generate recommendation based on scoring result."""
        score = result.overall_score
        confidence = result.confidence
        risk = result.risk.risk_level if result.risk else "MEDIUM"

        if score >= 8.0 and confidence >= 0.8 and risk in ("VERY_LOW", "LOW"):
            return "strong_publish"
        elif score >= 7.0 and confidence >= 0.7 and risk in ("VERY_LOW", "LOW", "MEDIUM"):
            return "publish"
        elif score >= 5.0 and confidence >= 0.5:
            return "conditional_publish"
        elif score >= 3.0:
            return "revise"
        return "skip"
