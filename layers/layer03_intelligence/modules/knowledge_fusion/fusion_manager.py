"""Fusion Manager - Orchestrator for Knowledge Fusion Module."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer03_intelligence.modules.knowledge_fusion.fusion_engine import FusionEngine, UnifiedIntelligence
from layers.layer03_intelligence.modules.knowledge_fusion.source_ranker import SourceRanker
from layers.layer03_intelligence.modules.knowledge_fusion.evidence_aggregator import EvidenceAggregator
from layers.layer03_intelligence.modules.knowledge_fusion.intelligence_merger import IntelligenceMerger


class FusionResult:
    __slots__ = ("topic", "unified", "source_ranks", "evidence", "merged", "recommendation", "timestamp")
    def __init__(self, topic: str = "") -> None:
        self.topic = topic
        self.unified: Optional[UnifiedIntelligence] = None
        self.source_ranks: List[Dict] = []
        self.evidence: Optional[Any] = None
        self.merged: Optional[Any] = None
        self.recommendation = ""
        self.timestamp = time.time()
    def to_dict(self) -> Dict:
        return {
            "topic": self.topic,
            "unified": self.unified.to_dict() if self.unified else None,
            "source_ranks": self.source_ranks,
            "evidence": self.evidence.to_dict() if self.evidence else None,
            "merged": self.merged.to_dict() if self.merged else None,
            "recommendation": self.recommendation,
            "timestamp": self.timestamp,
        }


class FusionManager:
    """Main orchestrator for knowledge fusion — combines ALL intelligence sources."""
    def __init__(self) -> None:
        self.fusion_engine = FusionEngine()
        self.source_ranker = SourceRanker()
        self.evidence_aggregator = EvidenceAggregator()
        self.intelligence_merger = IntelligenceMerger()

    def fuse(self, topic: str, data: Dict) -> FusionResult:
        result = FusionResult(topic)

        # Core fusion
        sources = data.get("sources", {})
        if sources:
            result.unified = self.fusion_engine.fuse(topic, sources)

        # Source ranking
        source_metrics = data.get("source_metrics", {})
        if source_metrics:
            ranked = self.source_ranker.rank(source_metrics)
            result.source_ranks = [s.to_dict() for s in ranked]

        # Evidence aggregation
        evidence_data = data.get("evidence", [])
        if evidence_data:
            result.evidence = self.evidence_aggregator.aggregate(topic, evidence_data)

        # Intelligence merging
        intelligences = data.get("intelligences", [])
        if intelligences:
            result.merged = self.intelligence_merger.merge(topic, intelligences)

        # Overall recommendation
        if result.unified:
            result.recommendation = result.unified.recommendation
        elif result.merged:
            conf = result.merged.confidence
            if conf > 0.7:
                result.recommendation = f"Strong unified intelligence for '{topic}'"
            else:
                result.recommendation = f"Limited intelligence for '{topic}' — need more sources"

        return result

    def fuse_batch(self, topics: Dict[str, Dict]) -> List[FusionResult]:
        return [self.fuse(topic, data) for topic, data in topics.items()]

    def get_health(self) -> Dict:
        return {
            "modules": ["FusionEngine", "SourceRanker", "EvidenceAggregator", "IntelligenceMerger"],
            "status": "healthy",
        }
