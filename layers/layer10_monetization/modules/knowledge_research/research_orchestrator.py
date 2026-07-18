"""ResearchOrchestrator — Complete research pipeline."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer10_monetization.modules.knowledge_research.research_manager import ResearchManager
from layers.layer10_monetization.modules.knowledge_research.trend_discovery import TrendDiscovery
from layers.layer10_monetization.modules.knowledge_research.competitor_intelligence import CompetitorIntelligence
from layers.layer10_monetization.modules.knowledge_research.audience_intelligence import AudienceIntelligence
from layers.layer10_monetization.modules.knowledge_research.market_intelligence import MarketIntelligence
from layers.layer10_monetization.modules.knowledge_research.knowledge_graph import KnowledgeGraph
from layers.layer10_monetization.modules.knowledge_research.fact_verifier import FactVerifier
from layers.layer10_monetization.modules.knowledge_research.research_memory import ResearchMemory
from layers.layer10_monetization.modules.knowledge_research.research_metrics import ResearchMetrics
from layers.layer10_monetization.modules.knowledge_research.research_validator import ResearchValidator
from layers.layer10_monetization.modules.knowledge_research.source_manager import SourceManager
from layers.layer10_monetization.modules.knowledge_research.research_report import ResearchReportGenerator


class ResearchOrchestrator:
    """Complete research pipeline.

    Flow: Request → Sources → Trends → Competitors → Audience → Market
          → Knowledge Graph → Facts → Memory → Validation → Metrics → Report
    """

    def __init__(self) -> None:
        self.manager = ResearchManager()
        self.trend_discovery = TrendDiscovery()
        self.competitor_intel = CompetitorIntelligence()
        self.audience_intel = AudienceIntelligence()
        self.market_intel = MarketIntelligence()
        self.knowledge_graph = KnowledgeGraph()
        self.fact_verifier = FactVerifier()
        self.memory = ResearchMemory()
        self.metrics = ResearchMetrics()
        self.validator = ResearchValidator()
        self.source_manager = SourceManager()
        self.report_generator = ResearchReportGenerator()
        self._pipeline_runs: List[Dict[str, Any]] = []

    def research(self, topic: str, platforms: Optional[List[str]] = None,
                 context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        start = time.time()
        platforms = platforms or ["universal"]
        context = context or {}
        results: Dict[str, Any] = {"topic": topic, "stages": {}}

        # Check memory first
        cached = self.memory.get_cached(topic)
        if cached:
            results["from_cache"] = True
            results["stages"]["cache"] = {"hit": True, "confidence": cached.confidence}
            return results

        # Stage 1: Trend discovery
        trends = self.trend_discovery.discover(topic, platforms[0])
        results["stages"]["trends"] = {"count": len(trends)}

        # Stage 2: Competitor intelligence
        for platform in platforms:
            self.competitor_intel.add_competitor(f"competitor_{platform}", platform)
        results["stages"]["competitors"] = {"count": len(platforms)}

        # Stage 3: Audience intelligence
        for platform in platforms:
            self.audience_intel.create_profile(platform)
        results["stages"]["audience"] = {"profiles": len(platforms)}

        # Stage 4: Market intelligence
        insights = [self.market_intel.analyze("industry", p) for p in platforms]
        results["stages"]["market"] = {"insights": len(insights)}

        # Stage 5: Knowledge graph
        entity = self.knowledge_graph.add_entity(topic, "topic")
        for t in trends:
            self.knowledge_graph.add_entity(t.topic, "trend")
            self.knowledge_graph.add_relationship(topic, t.topic, "has_trend")
        results["stages"]["knowledge"] = {"entities": len(self.knowledge_graph._entities)}

        # Stage 6: Fact verification
        verification = self.fact_verifier.verify(f"Topic {topic} is trending")
        results["stages"]["verification"] = verification.to_dict()

        # Stage 7: Store in memory
        self.memory.store(topic, {"trends": len(trends), "platforms": platforms},
                         confidence=verification.confidence)

        # Stage 8: Validate
        validation = self.validator.validate({"confidence": verification.confidence,
                                               "source_count": 1})
        results["stages"]["validation"] = validation.to_dict()

        # Stage 9: Metrics
        self.metrics.record_research(
            success=True, duration_ms=(time.time() - start) * 1000,
            accuracy=verification.confidence, api_calls=len(platforms),
        )

        # Stage 10: Report
        report = self.report_generator.generate("research", results)
        report.add_recommendation(f"Continue monitoring {topic}")

        results["duration_ms"] = round((time.time() - start) * 1000, 1)
        results["from_cache"] = False
        self._pipeline_runs.append(results)
        return results

    def get_health(self) -> Dict[str, Any]:
        return {
            "trends": self.trend_discovery.get_stats(),
            "competitors": self.competitor_intel.get_stats(),
            "audience": self.audience_intel.get_stats(),
            "market": self.market_intel.get_stats(),
            "knowledge": self.knowledge_graph.get_stats(),
            "memory": self.memory.get_stats(),
            "metrics": self.metrics.get_summary(),
            "pipeline_runs": len(self._pipeline_runs),
        }
