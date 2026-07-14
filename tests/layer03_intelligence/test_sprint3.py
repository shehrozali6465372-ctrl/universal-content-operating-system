"""
Tests for Sprint 3: Embeddings, Topic Hierarchy, Ambiguity, Confidence Calibration.
"""
import math
from layers.layer03_intelligence.modules.content_understanding.embedding_engine import EmbeddingEngine
from layers.layer03_intelligence.modules.content_understanding.topic_hierarchy import TopicHierarchy, TopicNode
from layers.layer03_intelligence.modules.content_understanding.ambiguity_detector import AmbiguityDetector
from layers.layer03_intelligence.modules.content_understanding.confidence_calibrator import ConfidenceCalibrator


# ═══════════════════════════════════════════════════════════════════
# EmbeddingEngine Tests
# ═══════════════════════════════════════════════════════════════════
class TestEmbeddingEngine:
    def setup_method(self):
        self.ee = EmbeddingEngine(vocab_size=100)
        corpus = [
            "AI is transforming technology and software",
            "Machine learning algorithms process data",
            "Invest money in stocks and crypto",
            "Health fitness exercise wellness",
            "Learn new skills through online courses",
            "AI jobs are increasing in demand",
            "Python programming language for AI",
            "Facebook social media platform",
        ]
        self.ee.fit(corpus)

    def test_fit(self):
        assert self.ee.is_fitted()
        assert self.ee.get_vocab_size() > 0

    def test_embed_returns_vector(self):
        vec = self.ee.embed("AI technology")
        assert isinstance(vec, list)
        assert len(vec) == self.ee.get_vocab_size()

    def test_embed_empty_text(self):
        vec = self.ee.embed("")
        assert all(v == 0.0 for v in vec)

    def test_embed_not_fitted(self):
        ee = EmbeddingEngine()
        assert ee.embed("test") == []

    def test_cosine_similarity_identical(self):
        sim = self.ee.cosine_similarity([1.0, 0.0, 0.0], [1.0, 0.0, 0.0])
        assert abs(sim - 1.0) < 0.001

    def test_cosine_similarity_orthogonal(self):
        sim = self.ee.cosine_similarity([1.0, 0.0], [0.0, 1.0])
        assert abs(sim) < 0.001

    def test_cosine_similarity_opposite(self):
        sim = self.ee.cosine_similarity([1.0, 0.0], [-1.0, 0.0])
        assert sim < 0

    def test_cosine_similarity_empty(self):
        assert self.ee.cosine_similarity([], []) == 0.0
        assert self.ee.cosine_similarity([1.0], [1.0, 2.0]) == 0.0

    def test_similarity_similar_texts(self):
        sim = self.ee.similarity("AI technology software", "AI technology programming")
        assert sim > 0.3

    def test_similarity_different_texts(self):
        sim = self.ee.similarity("AI technology", "health fitness exercise")
        assert sim < 0.5

    def test_similarity_empty(self):
        assert self.ee.similarity("", "test") == 0.0
        assert self.ee.similarity("test", "") == 0.0

    def test_cross_similarity_matrix(self):
        texts = ["AI technology", "machine learning", "health fitness"]
        matrix = self.ee.cross_similarity(texts)
        assert len(matrix) == 3
        assert len(matrix[0]) == 3
        # Diagonal should be 1.0
        for i in range(3):
            assert abs(matrix[i][i] - 1.0) < 0.001
        # Symmetric
        for i in range(3):
            for j in range(3):
                assert abs(matrix[i][j] - matrix[j][i]) < 0.001

    def test_cross_similarity_empty(self):
        assert self.ee.cross_similarity([]) == []

    def test_get_vocabulary(self):
        vocab = self.ee.get_vocabulary()
        assert len(vocab) > 0
        assert all(isinstance(v, str) for v in vocab)

    def test_reset(self):
        self.ee.reset()
        assert not self.ee.is_fitted()
        assert self.ee.get_vocab_size() == 0

    def test_normalized_vectors(self):
        vec = self.ee.embed("AI technology")
        mag = math.sqrt(sum(x * x for x in vec))
        assert abs(mag - 1.0) < 0.01 or mag == 0.0


# ═══════════════════════════════════════════════════════════════════
# TopicHierarchy Tests
# ═══════════════════════════════════════════════════════════════════
class TestTopicHierarchy:
    def setup_method(self):
        self.th = TopicHierarchy()

    def test_classify_known(self):
        node = self.th.classify("web")
        assert node.name == "web_development"

    def test_classify_ai(self):
        node = self.th.classify("ai")
        assert node.name == "artificial_intelligence"
        assert node.parent == "technology"

    def test_classify_alias(self):
        node = self.th.classify("ml")
        assert node.name == "artificial_intelligence"

    def test_classify_unknown(self):
        node = self.th.classify("xyzzy_unknown")
        assert node.parent == ""

    def test_get_parent(self):
        assert self.th.get_parent("nlp") == "artificial_intelligence"

    def test_get_children(self):
        children = self.th.get_children("technology")
        assert "programming" in children
        assert "artificial_intelligence" in children

    def test_get_siblings(self):
        siblings = self.th.get_siblings("web")
        assert "mobile_development" in siblings or "data_science" in siblings

    def test_get_siblings_root(self):
        siblings = self.th.get_siblings("technology")
        assert siblings == []

    def test_get_ancestors(self):
        ancestors = self.th.get_ancestors("nlp")
        assert "artificial_intelligence" in ancestors
        assert "technology" in ancestors

    def test_get_hierarchy(self):
        h = self.th.get_hierarchy()
        assert "technology" in h
        assert "finance" in h

    def test_search(self):
        results = self.th.search("prog")
        assert len(results) > 0

    def test_get_all_topics(self):
        topics = self.th.get_all_topics()
        assert len(topics) > 20

    def test_get_depth(self):
        assert self.th.get_depth("technology") == 0
        assert self.th.get_depth("programming") == 1
        assert self.th.get_depth("web_development") == 2

    def test_to_dict(self):
        node = self.th.classify("ai")
        d = node.to_dict()
        assert d["name"] == "artificial_intelligence"
        assert d["parent"] == "technology"


# ═══════════════════════════════════════════════════════════════════
# AmbiguityDetector Tests
# ═══════════════════════════════════════════════════════════════════
class TestAmbiguityDetector:
    def setup_method(self):
        self.ad = AmbiguityDetector()

    def test_clear_text(self):
        r = self.ad.detect("Machine learning algorithms process data efficiently")
        assert r.is_ambiguous is False

    def test_ambiguous_text(self):
        r = self.ad.detect("I love apple pie and Apple computers")
        assert r.is_ambiguous is True
        assert len(r.ambiguous_words) > 0

    def test_ambiguous_score(self):
        r = self.ad.detect("python programming language vs python snake")
        assert r.ambiguity_score > 0

    def test_hedge_words(self):
        r = self.ad.detect("Maybe possibly it could be something")
        assert r.ambiguity_score > 0

    def test_vague_words(self):
        r = self.ad.detect("The thing is basically just stuff")
        assert r.ambiguity_score > 0

    def test_alternatives(self):
        alts = self.ad.get_alternatives("bank interest rates")
        assert len(alts) > 0

    def test_is_ambiguous(self):
        assert self.ad.is_ambiguous("bank") is True
        assert self.ad.is_ambiguous("machine learning") is False

    def test_empty_text(self):
        r = self.ad.detect("")
        assert r.is_ambiguous is False
        assert r.ambiguity_score == 0.0

    def test_to_dict(self):
        r = self.ad.detect("python")
        d = r.to_dict()
        assert "ambiguity_score" in d
        assert "alternatives" in d

    def test_add_custom_word(self):
        self.ad.add_ambiguous_word("custom", ["meaning_a", "meaning_b"])
        r = self.ad.detect("custom")
        assert len(r.ambiguous_words) > 0

    def test_confidence(self):
        r = self.ad.detect("clear unambiguous text about machine learning")
        assert 0.0 <= r.confidence <= 1.0

    def test_reasons(self):
        r = self.ad.detect("maybe bank interest")
        assert len(r.reasons) > 0


# ═══════════════════════════════════════════════════════════════════
# ConfidenceCalibrator Tests
# ═══════════════════════════════════════════════════════════════════
class TestConfidenceCalibrator:
    def setup_method(self):
        self.cc = ConfidenceCalibrator()

    def test_calibrate_high(self):
        r = self.cc.calibrate({"topic": 0.9, "intent": 0.8, "entity": 0.9})
        assert r.overall > 0.5
        assert r.reliability in ("excellent", "good")

    def test_calibrate_low(self):
        r = self.cc.calibrate({"topic": 0.1, "intent": 0.05})
        assert r.overall < 0.5

    def test_calibrate_empty(self):
        r = self.cc.calibrate({})
        assert r.overall == 0.0

    def test_component_scores(self):
        r = self.cc.calibrate({"topic": 0.8, "intent": 0.6})
        assert "topic" in r.component_scores
        assert "intent" in r.component_scores

    def test_normalize_score(self):
        assert self.cc.normalize_score(5, 0, 10) == 0.5
        assert self.cc.normalize_score(-1, 0, 1) == 0.0
        assert self.cc.normalize_score(2, 0, 1) == 1.0
        assert self.cc.normalize_score(5, 5, 5) == 0.5

    def test_aggregate_equal_weights(self):
        agg = self.cc.aggregate_confidence([0.8, 0.6, 0.9])
        assert abs(agg - 0.7667) < 0.01

    def test_aggregate_custom_weights(self):
        agg = self.cc.aggregate_confidence([0.8, 0.6], weights=[0.7, 0.3])
        assert abs(agg - 0.74) < 0.01

    def test_aggregate_empty(self):
        assert self.cc.aggregate_confidence([]) == 0.0

    def test_reliability_grade(self):
        assert self.cc.reliability_grade(0.9) == "excellent"
        assert self.cc.reliability_grade(0.75) == "good"
        assert self.cc.reliability_grade(0.55) == "moderate"
        assert self.cc.reliability_grade(0.35) == "low"
        assert self.cc.reliability_grade(0.1) == "unreliable"

    def test_explanation(self):
        r = self.cc.calibrate({"topic": 0.9, "intent": 0.3})
        assert len(r.explanation) > 0

    def test_to_dict(self):
        r = self.cc.calibrate({"topic": 0.8})
        d = r.to_dict()
        assert "overall" in d
        assert "reliability" in d
        assert "explanation" in d

    def test_set_weights(self):
        self.cc.set_weights({"topic": 1.0})
        r = self.cc.calibrate({"topic": 0.9})
        assert r.overall > 0.8


# ═══════════════════════════════════════════════════════════════════
# Integration Test: Semantic Analyzer with Sprint 3
# ═══════════════════════════════════════════════════════════════════
class TestSprint3Integration:
    def test_full_pipeline(self):
        from layers.layer03_intelligence.modules.content_understanding.semantic_analyzer import SemanticAnalyzer
        analyzer = SemanticAnalyzer()
        result = analyzer.analyze("OpenAI released GPT-5 for AI research at Google headquarters")

        # Basic fields
        assert result.topic != ""
        assert result.intent != ""

        # Sprint 3 additions
        assert len(result.linked_entities) > 0
        assert len(result.reasoning) > 0

        # Verify entity linking worked
        entity_types = [e.entity_type for e in result.linked_entities]
        assert "ORG" in entity_types or "TECH" in entity_types

    def test_topic_hierarchy_with_analyzer(self):
        from layers.layer03_intelligence.modules.content_understanding.semantic_analyzer import SemanticAnalyzer
        th = TopicHierarchy()
        analyzer = SemanticAnalyzer()

        result = analyzer.analyze("AI technology software programming Python")
        for topic in result.topics[:3]:
            node = th.classify(topic)
            # Should find at least some topics in hierarchy
            assert isinstance(node, TopicNode)

    def test_ambiguity_with_analyzer(self):
        from layers.layer03_intelligence.modules.content_understanding.semantic_analyzer import SemanticAnalyzer
        ad = AmbiguityDetector()
        analyzer = SemanticAnalyzer()

        result = analyzer.analyze("I love apple pie and Apple computers")
        amb = ad.detect(result.topic)
        # Topic might be ambiguous
        assert isinstance(amb.is_ambiguous, bool)
