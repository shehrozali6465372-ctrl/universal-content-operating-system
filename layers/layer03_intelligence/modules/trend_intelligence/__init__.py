"""Trend Intelligence Module - Layer 3, Module 2."""
from layers.layer03_intelligence.modules.trend_intelligence.trend_manager import TrendManager
from layers.layer03_intelligence.modules.trend_intelligence.trend_collector import TrendCollector
from layers.layer03_intelligence.modules.trend_intelligence.trend_normalizer import TrendNormalizer
from layers.layer03_intelligence.modules.trend_intelligence.momentum_analyzer import MomentumAnalyzer
from layers.layer03_intelligence.modules.trend_intelligence.lifecycle_detector import LifecycleDetector
from layers.layer03_intelligence.modules.trend_intelligence.seasonality_analyzer import SeasonalityAnalyzer
from layers.layer03_intelligence.modules.trend_intelligence.virality_predictor import ViralityPredictor
from layers.layer03_intelligence.modules.trend_intelligence.cross_platform_fusion import CrossPlatformFusion
from layers.layer03_intelligence.modules.trend_intelligence.trend_confidence import TrendConfidence
from layers.layer03_intelligence.modules.trend_intelligence.trend_explainer import TrendExplainer
from layers.layer03_intelligence.modules.trend_intelligence.trend_predictor import TrendPredictor
from layers.layer03_intelligence.modules.trend_intelligence.trend_evidence import TrendEvidence, TrendEvidenceBuilder
from layers.layer03_intelligence.modules.trend_intelligence.trend_history import TrendHistory, TrendSnapshot
from layers.layer03_intelligence.modules.trend_intelligence.trend_events import TrendEventBus, TrendEventEmitter

__all__ = [
    "TrendManager", "TrendCollector", "TrendNormalizer", "MomentumAnalyzer",
    "LifecycleDetector", "SeasonalityAnalyzer", "ViralityPredictor",
    "CrossPlatformFusion", "TrendConfidence", "TrendExplainer", "TrendPredictor",
    "TrendEvidence", "TrendEvidenceBuilder", "TrendHistory", "TrendSnapshot",
    "TrendEventBus", "TrendEventEmitter",
]
