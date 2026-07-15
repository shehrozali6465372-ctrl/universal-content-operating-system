"""Tests for Layer 3, Module 7: Knowledge Fusion."""
from layers.layer03_intelligence.modules.knowledge_fusion import (
    FusionManager, FusionEngine, SourceRanker, EvidenceAggregator, IntelligenceMerger,
)


class TestFusionEngine:
    def test_fuse(self):
        engine = FusionEngine()
        ui = engine.fuse("AI Jobs", {"research": {"score": 0.9}, "trend": {"score": 0.8}})
        assert ui.topic == "AI Jobs"
        assert ui.confidence > 0
        assert len(ui.evidence) > 0
    def test_contradiction(self):
        engine = FusionEngine()
        ui = engine.fuse("X", {"a": {"score": 0.9}, "b": {"score": 0.1}})
        assert len(ui.contradictions) > 0
    def test_fuse_batch(self):
        engine = FusionEngine()
        results = engine.fuse_batch({"A": {"r": {"score": 0.8}}, "B": {"r": {"score": 0.6}}})
        assert len(results) == 2


class TestSourceRanker:
    def test_rank(self):
        r = SourceRanker()
        ranked = r.rank({"src1": {"reliability": 0.9}, "src2": {"reliability": 0.5}})
        assert ranked[0].name == "src1"


class TestEvidenceAggregator:
    def test_aggregate(self):
        agg = EvidenceAggregator()
        result = agg.aggregate("AI", [
            {"evidence": ["fact1", "fact2"], "source": "s1", "strength": 0.8},
            {"evidence": ["contra1"], "source": "s2", "strength": 0.2},
        ])
        assert len(result.supporting) == 2
        assert len(result.contradicting) == 1


class TestIntelligenceMerger:
    def test_merge(self):
        merger = IntelligenceMerger()
        result = merger.merge("AI", [{"score": 0.8, "topic": "AI"}, {"score": 0.6, "topic": "AI"}])
        assert result.source_count == 2
        assert result.merged_data["score"] == 0.7


class TestFusionManager:
    def setup_method(self):
        self.mgr = FusionManager()
    def test_full_fusion(self):
        result = self.mgr.fuse("AI Jobs", {
            "sources": {"research": {"score": 0.9}, "trend": {"score": 0.8}},
            "source_metrics": {"research": {"reliability": 0.9, "relevance": 0.8}},
            "evidence": [{"evidence": ["fact1"], "source": "r", "strength": 0.8}],
            "intelligences": [{"score": 0.85}],
        })
        assert result.unified is not None
        assert result.evidence is not None
        assert result.recommendation != ""
    def test_health(self):
        h = self.mgr.get_health()
        assert h["status"] == "healthy"
        assert len(h["modules"]) == 4
