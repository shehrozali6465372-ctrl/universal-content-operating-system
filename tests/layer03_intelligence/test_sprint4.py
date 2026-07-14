"""
Tests for Sprint 4: Contradiction, Clustering, Duplicates, Batch.
"""
from layers.layer03_intelligence.modules.content_understanding.contradiction_detector import (
    ContradictionDetector, ContradictionResult,
)
from layers.layer03_intelligence.modules.content_understanding.semantic_clusterer import (
    SemanticClusterer, Cluster,
)
from layers.layer03_intelligence.modules.content_understanding.duplicate_detector import (
    DuplicateDetector, DuplicateResult,
)
from layers.layer03_intelligence.modules.content_understanding.batch_processor import (
    BatchProcessor, BatchMetrics,
)


# ═══════════════════════════════════════════════════════════════════
# Contradiction Detector Tests
# ═══════════════════════════════════════════════════════════════════
class TestContradictionDetector:
    def setup_method(self):
        self.cd = ContradictionDetector()

    def test_no_contradiction(self):
        r = self.cd.detect("AI is great", "AI is wonderful")
        assert r.is_contradictory is False

    def test_antonym_contradiction(self):
        r = self.cd.detect("AI jobs are increasing", "AI jobs are declining")
        assert r.is_contradictory is True
        assert r.contradiction_type == "antonym"

    def test_negation_contradiction(self):
        r = self.cd.detect("AI will succeed", "AI will not succeed")
        assert r.is_contradictory is True
        assert r.contradiction_type == "negation"

    def test_directional_contradiction(self):
        r = self.cd.detect("Stock prices rise", "Stock prices fall")
        assert r.is_contradictory is True
        assert r.contradiction_type == "directional"

    def test_empty_text(self):
        r = self.cd.detect("", "AI is great")
        assert r.is_contradictory is False

    def test_both_empty(self):
        r = self.cd.detect("", "")
        assert r.is_contradictory is False

    def test_has_contradiction(self):
        assert self.cd.has_contradiction("AI increases", "AI decreases") is True
        assert self.cd.has_contradiction("AI is good", "AI is great") is False

    def test_has_contradiction_threshold(self):
        assert self.cd.has_contradiction("AI increases", "AI decreases", 0.3) is True

    def test_detect_batch(self):
        texts = [
            "AI jobs are increasing",
            "AI jobs are declining",
            "Python is popular",
        ]
        results = self.cd.detect_batch(texts)
        assert len(results) >= 1

    def test_find_contradictions(self):
        texts = [
            "AI is growing fast",
            "AI is declining fast",
            "Python is popular",
        ]
        pairs = self.cd.find_contradictions(texts)
        assert len(pairs) >= 1
        assert (0, 1) in pairs

    def test_add_custom_antonym(self):
        self.cd.add_antonym_pair("upbeat", "downbeat")
        r = self.cd.detect("The mood is upbeat", "The mood is downbeat")
        assert r.is_contradictory is True

    def test_to_dict(self):
        r = self.cd.detect("AI rises", "AI falls")
        d = r.to_dict()
        assert "is_contradictory" in d
        assert "contradiction_type" in d
        assert "explanation" in d

    def test_same_sentiment_no_contradiction(self):
        r = self.cd.detect("AI is excellent", "AI is wonderful")
        assert r.is_contradictory is False


# ═══════════════════════════════════════════════════════════════════
# Semantic Clusterer Tests
# ═══════════════════════════════════════════════════════════════════
class TestSemanticClusterer:
    def setup_method(self):
        self.sc = SemanticClusterer()

    def test_cluster_empty(self):
        assert self.sc.cluster([]) == []

    def test_cluster_single(self):
        clusters = self.sc.cluster(["AI technology"])
        assert len(clusters) == 1
        assert clusters[0].size == 1

    def test_cluster_similar(self):
        clusters = self.sc.cluster([
            "AI technology software",
            "AI technology programming",
            "AI technology development",
        ], threshold=0.3)
        assert len(clusters) >= 1

    def test_cluster_different(self):
        clusters = self.sc.cluster([
            "AI technology software programming",
            "Cooking recipes food ingredients kitchen",
            "Financial investment stock market",
        ], threshold=0.1)
        assert len(clusters) >= 2

    def test_cluster_mixed(self):
        clusters = self.sc.cluster([
            "AI technology",
            "machine learning AI",
            "cooking recipes",
            "food recipes",
        ], threshold=0.2)
        assert len(clusters) >= 2

    def test_assign(self):
        self.sc.cluster(["AI technology software"], threshold=0.3)
        assigned = self.sc.assign("AI technology programming")
        assert assigned >= 0

    def test_assign_no_match(self):
        self.sc.cluster(["cooking food recipes"], threshold=0.3)
        assigned = self.sc.assign("quantum physics equations")
        assert assigned == -1

    def test_get_cluster(self):
        self.sc.cluster(["AI tech", "AI software"], threshold=0.3)
        clusters = self.sc.get_clusters()
        assert len(clusters) >= 1
        c = self.sc.get_cluster(clusters[0].cluster_id)
        assert c is not None

    def test_merge_clusters(self):
        self.sc.cluster(["AI tech", "cooking food"], threshold=0.1)
        clusters = self.sc.get_clusters()
        if len(clusters) >= 2:
            self.sc.merge_clusters(clusters[0].cluster_id, clusters[1].cluster_id)
            assert len(self.sc.get_clusters()) < len(clusters)

    def test_summary(self):
        self.sc.cluster(["AI tech", "AI software", "cooking food"], threshold=0.3)
        s = self.sc.summary()
        assert "total_clusters" in s
        assert "total_texts" in s

    def test_reset(self):
        self.sc.cluster(["test"])
        self.sc.reset()
        assert self.sc.summary()["total_clusters"] == 0

    def test_cluster_label(self):
        clusters = self.sc.cluster(["hello world testing"], threshold=0.3)
        assert clusters[0].label != ""

    def test_to_dict(self):
        clusters = self.sc.cluster(["test text"], threshold=0.3)
        d = clusters[0].to_dict()
        assert "cluster_id" in d
        assert "label" in d


# ═══════════════════════════════════════════════════════════════════
# Duplicate Detector Tests
# ═══════════════════════════════════════════════════════════════════
class TestDuplicateDetector:
    def setup_method(self):
        self.dd = DuplicateDetector()

    def test_same_meaning(self):
        r = self.dd.detect("AI is amazing", "artificial intelligence is wonderful")
        assert r.is_duplicate is True
        assert r.similarity > 0.3

    def test_different_meaning(self):
        r = self.dd.detect("AI is growing", "cooking recipes for dinner")
        assert r.is_duplicate is False

    def test_exact_same(self):
        r = self.dd.detect("hello world", "hello world")
        assert r.is_duplicate is True
        assert r.similarity >= 0.9

    def test_empty(self):
        r = self.dd.detect("", "hello")
        assert r.is_duplicate is False

    def test_find_duplicates(self):
        texts = [
            "AI is amazing",
            "artificial intelligence is wonderful",
            "cooking recipes food",
        ]
        pairs = self.dd.find_duplicates(texts)
        assert len(pairs) >= 1
        assert (0, 1) in pairs

    def test_deduplicate(self):
        texts = [
            "AI is great",
            "artificial intelligence is excellent",
            "cooking is fun",
        ]
        unique = self.dd.deduplicate(texts)
        assert len(unique) <= len(texts)

    def test_get_groups(self):
        texts = [
            "AI technology",
            "artificial intelligence tech",
            "cooking food",
            "culinary dishes",
        ]
        groups = self.dd.get_groups(texts, threshold=0.3)
        assert len(groups) >= 2

    def test_to_dict(self):
        r = self.dd.detect("AI great", "AI excellent")
        d = r.to_dict()
        assert "similarity" in d
        assert "synonym_matches" in d

    def test_add_synonym(self):
        self.dd.add_synonym_group({"alpha", "beta", "gamma"})
        r = self.dd.detect("alpha system", "gamma system")
        assert len(r.synonym_matches) > 0

    def test_synonym_matches(self):
        r = self.dd.detect("buy a car", "purchase a vehicle")
        assert len(r.synonym_matches) > 0


# ═══════════════════════════════════════════════════════════════════
# Batch Processor Tests
# ═══════════════════════════════════════════════════════════════════
class TestBatchProcessor:
    def setup_method(self):
        self.bp = BatchProcessor()

    def test_analyze_many(self):
        results = self.bp.analyze_many(["AI tech", "cooking food", "finance money"])
        assert len(results) == 3

    def test_analyze_many_empty(self):
        results = self.bp.analyze_many([])
        assert results == []

    def test_analyze_with_cache(self):
        r1 = self.bp.analyze_with_cache("AI technology")
        r2 = self.bp.analyze_with_cache("AI technology")
        assert r1 is r2  # Same cached object

    def test_cache_size(self):
        self.bp.analyze_with_cache("text1")
        self.bp.analyze_with_cache("text2")
        assert self.bp.cache_size() == 2

    def test_clear_cache(self):
        self.bp.analyze_with_cache("text1")
        self.bp.clear_cache()
        assert self.bp.cache_size() == 0

    def test_metrics(self):
        self.bp.analyze_many(["AI tech", "cooking food"])
        m = self.bp.get_metrics()
        assert m["total_analyses"] == 2
        assert m["cache_hits"] == 0
        assert m["cache_misses"] == 2

    def test_cache_hit_metrics(self):
        self.bp.analyze_with_cache("test text")
        self.bp.analyze_with_cache("test text")
        m = self.bp.get_metrics()
        assert m["cache_hits"] == 1
        assert m["cache_misses"] == 1

    def test_reset_metrics(self):
        self.bp.analyze_many(["test"])
        self.bp.reset_metrics()
        m = self.bp.get_metrics()
        assert m["total_analyses"] == 0

    def test_metrics_performance(self):
        self.bp.analyze_many(["AI tech"] * 10)
        m = self.bp.get_metrics()
        assert m["texts_per_second"] > 0

    def test_metrics_to_dict(self):
        self.bp.analyze_many(["test"])
        m = self.bp.get_metrics()
        assert "total_analyses" in m
        assert "avg_time_ms" in m


class TestBatchMetrics:
    def test_record(self):
        m = BatchMetrics()
        m.record(10.0, cached=False)
        assert m.total_analyses == 1
        assert m.cache_misses == 1

    def test_record_cached(self):
        m = BatchMetrics()
        m.record(0.0, cached=True)
        assert m.cache_hits == 1

    def test_to_dict(self):
        m = BatchMetrics()
        m.record(10.0)
        d = m.to_dict()
        assert "total_analyses" in d
        assert "cache_hit_rate" in d
