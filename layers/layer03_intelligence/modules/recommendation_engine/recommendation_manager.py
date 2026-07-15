"""Recommendation Manager - Orchestrator for Recommendation Engine Module."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer03_intelligence.modules.recommendation_engine.candidate_generator import CandidateGenerator
from layers.layer03_intelligence.modules.recommendation_engine.ranking_engine import RankingEngine
from layers.layer03_intelligence.modules.recommendation_engine.constraint_filter import ConstraintFilter
from layers.layer03_intelligence.modules.recommendation_engine.diversity_engine import DiversityEngine
from layers.layer03_intelligence.modules.recommendation_engine.novelty_engine import NoveltyEngine
from layers.layer03_intelligence.modules.recommendation_engine.explanation_builder import ExplanationBuilder
from layers.layer03_intelligence.modules.recommendation_engine.confidence_calculator import ConfidenceCalculator
from layers.layer03_intelligence.modules.recommendation_engine.recommendation_memory import RecommendationMemory
from layers.layer03_intelligence.modules.recommendation_engine.feedback_collector import FeedbackCollector


class RecommendationResult:
    __slots__ = ("recommendations", "explanations", "confidence", "diversity",
                 "filtered_count", "total_candidates", "recommendation", "timestamp")

    def __init__(self) -> None:
        self.recommendations: List[Dict] = []
        self.explanations: List[Dict] = []
        self.confidence: Optional[Any] = None
        self.diversity: Optional[Any] = None
        self.filtered_count = 0
        self.total_candidates = 0
        self.recommendation = ""
        self.timestamp = time.time()

    def to_dict(self) -> Dict:
        return {
            "recommendations": self.recommendations,
            "explanations": self.explanations,
            "confidence": self.confidence.to_dict() if self.confidence else None,
            "diversity": self.diversity.to_dict() if self.diversity else None,
            "filtered_count": self.filtered_count,
            "total_candidates": self.total_candidates,
            "recommendation": self.recommendation,
            "timestamp": self.timestamp,
        }


class RecommendationManager:
    """Main orchestrator for recommendation generation.

    Usage::

        manager = RecommendationManager()
        result = manager.recommend({
            "trends": [{"topic": "AI Jobs", "score": 0.9, "momentum": 0.8}],
            "audience_gaps": [{"topic": "AI Career", "demand": 0.8}],
            "max_results": 3,
        })
    """

    def __init__(self) -> None:
        self.generator = CandidateGenerator()
        self.ranker = RankingEngine()
        self.filter = ConstraintFilter()
        self.diversity = DiversityEngine()
        self.novelty = NoveltyEngine()
        self.explainer = ExplanationBuilder()
        self.confidence_calc = ConfidenceCalculator()
        self.memory = RecommendationMemory()
        self.feedback = FeedbackCollector()

    def recommend(self, data: Dict) -> RecommendationResult:
        result = RecommendationResult()

        # Generate candidates
        all_candidates = []
        if "trends" in data:
            all_candidates.extend(self.generator.generate_from_trends(data["trends"]))
        if "audience_gaps" in data:
            all_candidates.extend(self.generator.generate_from_audience(data["audience_gaps"]))
        if "competitor_gaps" in data:
            all_candidates.extend(self.generator.generate_from_competitor(data["competitor_gaps"]))
        if "knowledge" in data:
            all_candidates.extend(self.generator.generate_from_knowledge(data["knowledge"]))

        result.total_candidates = len(all_candidates)
        if not all_candidates:
            result.recommendation = "No candidates available"
            return result

        # Filter
        filter_result = self.filter.filter(all_candidates)
        result.filtered_count = len(filter_result.filtered_out)
        candidates = filter_result.passed if filter_result.passed else all_candidates

        # Rank
        ranked = self.ranker.rank(candidates)

        # Diversify
        div_result = self.diversity.diversify(ranked)
        result.diversity = div_result
        candidates = div_result.selected if div_result.selected else ranked

        # Take top N
        max_n = data.get("max_results", 5)
        top = candidates[:max_n]

        # Build recommendations with explanations
        for c in top:
            exp = self.explainer.build(c)
            rec = {
                "recommendation": c.topic,
                "score": round(getattr(c, "final_score", getattr(c, "base_score", 0)), 3),
                "source": c.source,
                "why": exp.why,
                "why_not": exp.why_not,
            }
            result.recommendations.append(rec)
            result.explanations.append(exp.to_dict())

            # Store in memory
            self.memory.store(RecRecord(c.topic, c.final_score if hasattr(c, "final_score") else c.base_score))

        # Confidence
        if top:
            avg_score = sum(r["score"] for r in result.recommendations) / len(result.recommendations)
            result.confidence = self.confidence_calc.calculate({"overall": avg_score})

        # Recommendation text
        if result.recommendations:
            best = result.recommendations[0]
            result.recommendation = f"Recommended: '{best['recommendation']}' (score: {best['score']:.0%})"

        return result

    def get_health(self) -> Dict:
        return {
            "modules": ["CandidateGenerator", "RankingEngine", "ConstraintFilter",
                       "DiversityEngine", "NoveltyEngine", "ExplanationBuilder",
                       "ConfidenceCalculator", "RecommendationMemory", "FeedbackCollector"],
            "status": "healthy",
            "candidates_generated": self.memory.count(),
            "success_rate": round(self.memory.get_success_rate(), 3),
        }


# Need this for memory
from layers.layer03_intelligence.modules.recommendation_engine.recommendation_memory import RecRecord
