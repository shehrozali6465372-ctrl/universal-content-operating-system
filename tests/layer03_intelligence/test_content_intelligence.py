"""Tests for Layer 3, Module 4: Content Intelligence."""
from layers.layer03_intelligence.modules.content_intelligence import (
    IntelligenceManager, QualityEstimator, ReadabilityAnalyzer,
    EmotionalAnalyzer, ContentViralityPredictor, AudienceFitAnalyzer,
    NoveltyDetector, RedundancyDetector, HookAnalyzer, CTAAnalyzer,
    ContentOptimizer, ContentConfidence,
)

SAMPLE = "AI jobs are amazing! How to start your career in 2026? Check our guide. Like and share!"


class TestQualityEstimator:
    def test_estimate(self):
        r = QualityEstimator().estimate(SAMPLE)
        assert 0 <= r.overall_score <= 1
        assert r.grade in ("A+", "A", "B", "C", "D")
    def test_empty(self):
        r = QualityEstimator().estimate("")
        assert r.overall_score <= 0.5

class TestReadabilityAnalyzer:
    def test_analyze(self):
        r = ReadabilityAnalyzer().analyze(SAMPLE)
        assert 0 <= r.flesch_score <= 100
        assert r.word_count > 0
        assert r.complexity in ("easy", "moderate", "difficult", "very_difficult")
    def test_empty(self):
        r = ReadabilityAnalyzer().analyze("")
        assert r.word_count == 0

class TestEmotionalAnalyzer:
    def test_positive(self):
        r = EmotionalAnalyzer().analyze("This is amazing and wonderful! Best day ever!")
        assert r.sentiment == "positive"
    def test_negative(self):
        r = EmotionalAnalyzer().analyze("This is terrible and horrible. Worst experience.")
        assert r.sentiment == "negative"
    def test_dominant_emotion(self):
        r = EmotionalAnalyzer().analyze(SAMPLE)
        assert r.dominant_emotion != ""

class TestContentViralityPredictor:
    def test_predict(self):
        r = ContentViralityPredictor().predict(SAMPLE)
        assert 0 <= r.virality_score <= 1
        assert r.hook_strength >= 0
    def test_empty(self):
        r = ContentViralityPredictor().predict("")
        assert r.virality_score >= 0

class TestAudienceFitAnalyzer:
    def test_fit(self):
        r = AudienceFitAnalyzer().analyze(SAMPLE, {"interests": ["technology", "career"], "reading_level": "moderate"})
        assert 0 <= r.fit_score <= 1

class TestNoveltyDetector:
    def test_novel(self):
        d = NoveltyDetector()
        r = d.detect("Completely unique content about quantum physics")
        assert r.is_novel is True
    def test_duplicate(self):
        d = NoveltyDetector()
        d.detect("Same content here")
        r = d.detect("Same content here")
        assert r.novelty_score == 0

class TestRedundancyDetector:
    def test_no_redundancy(self):
        r = RedundancyDetector().detect("The quick brown fox jumps over the lazy dog")
        assert r.redundancy_score < 0.5
    def test_redundancy(self):
        r = RedundancyDetector().detect("the the the the the the the the the the the")
        assert r.redundancy_score > 0

class TestHookAnalyzer:
    def test_question_hook(self):
        r = HookAnalyzer().analyze("How to become a successful AI developer?")
        assert r.hook_type == "question"
    def test_score(self):
        r = HookAnalyzer().analyze(SAMPLE)
        assert 0 <= r.hook_score <= 1

class TestCTAAnalyzer:
    def test_has_cta(self):
        r = CTAAnalyzer().analyze("Great content. Like and share this post!")
        assert r.has_cta is True
    def test_no_cta(self):
        r = CTAAnalyzer().analyze("Just some text without any action words.")
        assert r.has_cta is False

class TestContentOptimizer:
    def test_optimize(self):
        r = ContentOptimizer().optimize(SAMPLE, {"quality": 0.6, "engagement": 0.4})
        assert r.improvement >= 0
        assert len(r.suggestions) > 0

class TestContentConfidence:
    def test_high(self):
        r = ContentConfidence().calculate({"quality": 0.9, "readability": 0.8, "engagement": 0.7})
        assert r.overall > 0.7
        assert r.risk_level == "low"
    def test_low(self):
        r = ContentConfidence().calculate({"quality": 0.2, "readability": 0.1})
        assert r.risk_level == "high"

class TestIntelligenceManager:
    def setup_method(self):
        self.mgr = IntelligenceManager()
    def test_full_analysis(self):
        result = self.mgr.analyze(SAMPLE, {"interests": ["AI", "career"]})
        assert result.quality is not None
        assert result.readability is not None
        assert result.emotion is not None
        assert result.hook is not None
        assert result.confidence is not None
        assert result.recommendation != ""
    def test_health(self):
        h = self.mgr.get_health()
        assert h["status"] == "healthy"
        assert len(h["modules"]) == 11
    def test_to_dict(self):
        result = self.mgr.analyze(SAMPLE)
        d = result.to_dict()
        assert "quality" in d
        assert "confidence" in d
