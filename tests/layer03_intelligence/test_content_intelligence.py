"""Tests for Module 4: Content Intelligence."""
from layers.layer03_intelligence.modules.content_intelligence.quality_estimator import QualityEstimator
from layers.layer03_intelligence.modules.content_intelligence.virality_predictor import ViralityPredictor
from layers.layer03_intelligence.modules.content_intelligence.audience_fit import AudienceFitAnalyzer


class TestQualityEstimator:
    def setup_method(self): self.qe = QualityEstimator()
    def test_estimate(self):
        r = self.qe.estimate("This is a great post about AI technology and software development #AI")
        assert r.score > 0
        assert r.grade in ("A", "B", "C", "D", "F")
    def test_estimate_empty(self):
        r = self.qe.estimate("")
        assert r.score < 0.5
    def test_to_dict(self):
        r = self.qe.estimate("Test content here")
        d = r.to_dict()
        assert "score" in d
        assert "grade" in d


class TestViralityPredictor:
    def setup_method(self): self.vp = ViralityPredictor()
    def test_predict_viral(self):
        r = self.vp.predict("This is absolutely amazing! You won't believe the secret revealed!")
        assert r.virality_score > 0
        assert r.emotional_appeal > 0
    def test_predict_boring(self):
        r = self.vp.predict("The quarterly report was submitted")
        assert r.virality_score >= 0
    def test_to_dict(self):
        r = self.vp.predict("Amazing secret!")
        d = r.to_dict()
        assert "virality_score" in d


class TestAudienceFitAnalyzer:
    def setup_method(self): self.af = AudienceFitAnalyzer()
    def test_strong_fit(self):
        r = self.af.analyze(["ai", "tech", "software"], ["ai", "tech", "programming"])
        assert r.fit_score >= 0.5
        assert r.recommendation in ("strong_fit", "moderate_fit")
    def test_weak_fit(self):
        r = self.af.analyze(["cooking", "recipe"], ["ai", "tech"])
        assert r.fit_score < 0.5
    def test_with_demographics(self):
        r = self.af.analyze(["ai"], ["ai"], {"age": "25-34", "location": "US"})
        assert r.fit_score > 0
