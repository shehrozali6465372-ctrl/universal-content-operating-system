"""Tests for Module 2: Trend Intelligence."""
from layers.layer03_intelligence.modules.trend_intelligence.trend_predictor import TrendPredictor
from layers.layer03_intelligence.modules.trend_intelligence.momentum_analyzer import MomentumAnalyzer
from layers.layer03_intelligence.modules.trend_intelligence.lifecycle_detector import LifecycleDetector, LifecycleStage


class TestTrendPredictor:
    def setup_method(self): self.tp = TrendPredictor()
    def test_predict_rising(self):
        p = self.tp.predict("AI", [20, 40, 60, 80])
        assert p.predicted_direction == "rising"
        assert p.predicted_score > 80
    def test_predict_falling(self):
        p = self.tp.predict("old_trend", [80, 60, 40, 20])
        assert p.predicted_direction == "falling"
    def test_predict_stable(self):
        p = self.tp.predict("stable", [50, 50, 50, 50])
        assert p.predicted_direction in ("stable", "peak")
    def test_predict_short_history(self):
        p = self.tp.predict("new", [60])
        assert p.predicted_direction == "stable"
    def test_predict_batch(self):
        preds = self.tp.predict_batch({"AI": [10, 30, 50], "Crypto": [50, 40, 30]})
        assert len(preds) == 2
    def test_rank_by_opportunity(self):
        preds = [
            self.tp.predict("rising", [10, 20, 30, 40, 50, 60]),
            self.tp.predict("falling", [60, 50, 40, 30, 20, 10]),
        ]
        ranked = self.tp.rank_by_opportunity(preds)
        assert ranked[0].predicted_direction == "rising"


class TestMomentumAnalyzer:
    def setup_method(self): self.ma = MomentumAnalyzer()
    def test_positive_momentum(self):
        r = self.ma.analyze([10, 20, 30, 40])
        assert r.velocity > 0
        assert r.momentum_score > 50
    def test_negative_momentum(self):
        r = self.ma.analyze([40, 30, 20, 10])
        assert r.velocity < 0
    def test_zero_momentum(self):
        r = self.ma.analyze([50, 50, 50])
        assert r.velocity == 0
    def test_short_history(self):
        r = self.ma.analyze([50])
        assert r.velocity == 0


class TestLifecycleDetector:
    def setup_method(self): self.ld = LifecycleDetector()
    def test_emerging(self):
        r = self.ld.detect([10, 15, 20, 25])
        assert r.stage in (LifecycleStage.EMERGING, LifecycleStage.GROWING)
    def test_peak(self):
        r = self.ld.detect([20, 50, 80, 80, 80])
        assert r.stage in (LifecycleStage.PEAK, LifecycleStage.GROWING)
    def test_declining(self):
        r = self.ld.detect([80, 60, 40, 20, 10])
        assert r.stage in (LifecycleStage.DECLINING, LifecycleStage.DEAD)
    def test_short_data(self):
        r = self.ld.detect([50, 60])
        assert r.stage == LifecycleStage.EMERGING
