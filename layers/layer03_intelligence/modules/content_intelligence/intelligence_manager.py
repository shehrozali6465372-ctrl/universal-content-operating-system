"""Content Intelligence Manager - Orchestrator for Content Intelligence Module."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer03_intelligence.modules.content_intelligence.quality_estimator import QualityEstimator
from layers.layer03_intelligence.modules.content_intelligence.readability_analyzer import ReadabilityAnalyzer
from layers.layer03_intelligence.modules.content_intelligence.emotional_analyzer import EmotionalAnalyzer
from layers.layer03_intelligence.modules.content_intelligence.virality_predictor import ContentViralityPredictor
from layers.layer03_intelligence.modules.content_intelligence.audience_fit_analyzer import AudienceFitAnalyzer
from layers.layer03_intelligence.modules.content_intelligence.novelty_detector import NoveltyDetector
from layers.layer03_intelligence.modules.content_intelligence.redundancy_detector import RedundancyDetector
from layers.layer03_intelligence.modules.content_intelligence.hook_analyzer import HookAnalyzer
from layers.layer03_intelligence.modules.content_intelligence.cta_analyzer import CTAAnalyzer
from layers.layer03_intelligence.modules.content_intelligence.content_optimizer import ContentOptimizer
from layers.layer03_intelligence.modules.content_intelligence.content_confidence import ContentConfidence


class ContentAnalysisResult:
    __slots__ = ("content", "quality", "readability", "emotion", "virality",
                 "audience_fit", "novelty", "redundancy", "hook", "cta",
                 "optimization", "confidence", "recommendation", "timestamp")

    def __init__(self, content: str = "") -> None:
        self.content = content[:200]
        self.quality: Optional[Any] = None
        self.readability: Optional[Any] = None
        self.emotion: Optional[Any] = None
        self.virality: Optional[Any] = None
        self.audience_fit: Optional[Any] = None
        self.novelty: Optional[Any] = None
        self.redundancy: Optional[Any] = None
        self.hook: Optional[Any] = None
        self.cta: Optional[Any] = None
        self.optimization: Optional[Any] = None
        self.confidence: Optional[Any] = None
        self.recommendation = ""
        self.timestamp = time.time()

    def to_dict(self) -> Dict:
        return {
            "content_preview": self.content, "timestamp": self.timestamp,
            "quality": self.quality.to_dict() if self.quality else None,
            "readability": self.readability.to_dict() if self.readability else None,
            "emotion": self.emotion.to_dict() if self.emotion else None,
            "virality": self.virality.to_dict() if self.virality else None,
            "audience_fit": self.audience_fit.to_dict() if self.audience_fit else None,
            "novelty": self.novelty.to_dict() if self.novelty else None,
            "redundancy": self.redundancy.to_dict() if self.redundancy else None,
            "hook": self.hook.to_dict() if self.hook else None,
            "cta": self.cta.to_dict() if self.cta else None,
            "optimization": self.optimization.to_dict() if self.optimization else None,
            "confidence": self.confidence.to_dict() if self.confidence else None,
            "recommendation": self.recommendation,
        }


class IntelligenceManager:
    def __init__(self) -> None:
        self.quality = QualityEstimator()
        self.readability = ReadabilityAnalyzer()
        self.emotion = EmotionalAnalyzer()
        self.virality = ContentViralityPredictor()
        self.audience_fit = AudienceFitAnalyzer()
        self.novelty = NoveltyDetector()
        self.redundancy = RedundancyDetector()
        self.hook = HookAnalyzer()
        self.cta = CTAAnalyzer()
        self.optimizer = ContentOptimizer()
        self.confidence = ContentConfidence()

    def analyze(self, content: str, audience: Optional[Dict] = None,
                existing_content: Optional[List[str]] = None) -> ContentAnalysisResult:
        result = ContentAnalysisResult(content)
        audience = audience or {}

        result.quality = self.quality.estimate(content)
        result.readability = self.readability.analyze(content)
        result.emotion = self.emotion.analyze(content)
        result.virality = self.virality.predict(content)
        result.audience_fit = self.audience_fit.analyze(content, audience)
        result.novelty = self.novelty.detect(content, existing_content)
        result.redundancy = self.redundancy.detect(content)
        result.hook = self.hook.analyze(content)
        result.cta = self.cta.analyze(content)

        scores = {
            "quality": result.quality.overall_score,
            "readability": result.readability.flesch_score / 100,
            "engagement": result.emotion.emotional_intensity,
            "novelty": result.novelty.novelty_score,
            "relevance": result.audience_fit.fit_score,
            "virality": result.virality.virality_score,
        }
        result.optimization = self.optimizer.optimize(content, scores)
        result.confidence = self.confidence.calculate(scores)

        # Recommendation
        if result.confidence and result.confidence.overall >= 0.7:
            result.recommendation = "Content is ready for publishing"
        elif result.optimization and result.optimization.improvement > 0.2:
            result.recommendation = f"Apply optimizations to improve by {result.optimization.improvement:.0%}"
        else:
            result.recommendation = "Consider revisions before publishing"

        return result

    def get_health(self) -> Dict:
        return {
            "modules": ["QualityEstimator", "ReadabilityAnalyzer", "EmotionalAnalyzer",
                       "ContentViralityPredictor", "AudienceFitAnalyzer", "NoveltyDetector",
                       "RedundancyDetector", "HookAnalyzer", "CTAAnalyzer",
                       "ContentOptimizer", "ContentConfidence"],
            "status": "healthy",
        }
