"""Knowledge Fusion Module - Layer 3, Module 7."""
from layers.layer03_intelligence.modules.knowledge_fusion.fusion_manager import FusionManager
from layers.layer03_intelligence.modules.knowledge_fusion.fusion_engine import FusionEngine, UnifiedIntelligence
from layers.layer03_intelligence.modules.knowledge_fusion.source_ranker import SourceRanker
from layers.layer03_intelligence.modules.knowledge_fusion.evidence_aggregator import EvidenceAggregator
from layers.layer03_intelligence.modules.knowledge_fusion.intelligence_merger import IntelligenceMerger

__all__ = [
    "FusionManager", "FusionEngine", "UnifiedIntelligence",
    "SourceRanker", "EvidenceAggregator", "IntelligenceMerger",
]
