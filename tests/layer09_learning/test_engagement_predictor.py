"""Tests for Layer 9 Module 9 — Engagement Predictor Engine."""
from layers.layer09_learning.modules.engagement_predictor.prediction_profile import (
    PredictionProfile, PREDICTION_HORIZONS, CONFIDENCE_LEVELS,
)
from layers.layer09_learning.modules.engagement_predictor.feature_extractor import (
    FeatureExtractor, ContentFeatures,
)
from layers.layer09_learning.modules.engagement_predictor.engagement_model import (
    EngagementModel, EngagementPrediction,
)
from layers.layer09_learning.modules.engagement_predictor.virality_estimator import (
    ViralityEstimator,
)
from layers.layer09_learning.modules.engagement_predictor.timing_optimizer import (
    TimingOptimizer, TimeSlot,
)
from layers.layer09_learning.modules.engagement_predictor.audience_predictor import (
    AudiencePredictor,
)
from layers.layer09_learning.modules.engagement_predictor.prediction_memory import (
    PredictionMemory,
)
from layers.layer09_learning.modules.engagement_predictor.prediction_metrics import PredictionMetrics
from layers.layer09_learning.modules.engagement_predictor.prediction_validator import (
    PredictionValidator,
)
from layers.layer09_learning.modules.engagement_predictor.engagement_manager import (
    EngagementManager,
)
from layers.layer09_learning.modules.engagement_predictor.exceptions import (
    EngagementPredictionError, FeatureExtractionError, PredictionError, ValidationError,
)


# ─── PredictionProfile Tests ──────────────────────────────────────
class TestPredictionProfile:
    def test_create_default(self):
        p = PredictionProfile()
        assert p.profile_id.startswith("pp_")
        assert p.horizon == "24h"
        assert p.confidence_level == "medium"
        assert p.include_virality is True
        assert p.include_timing is True
        assert p.include_audience is True

    def test_custom_horizon(self):
        p = PredictionProfile(horizon="7d")
        assert p.horizon == "7d"

    def test_invalid_horizon(self):
        p = PredictionProfile(horizon="invalid")
        assert p.horizon == "24h"

    def test_custom_confidence(self):
        p = PredictionProfile(confidence_level="high")
        assert p.confidence_level == "high"

    def test_invalid_confidence(self):
        p = PredictionProfile(confidence_level="super_high")
        assert p.confidence_level == "medium"

    def test_to_dict(self):
        p = PredictionProfile(platform="facebook", content_type="post")
        d = p.to_dict()
        assert d["profile_id"].startswith("pp_")
        assert d["horizon"] == "24h"
        assert d["platform"] == "facebook"
        assert d["content_type"] == "post"

    def test_horizons_defined(self):
        assert "immediate" in PREDICTION_HORIZONS
        assert "24h" in PREDICTION_HORIZONS
        assert "7d" in PREDICTION_HORIZONS
        assert "30d" in PREDICTION_HORIZONS

    def test_confidence_levels_defined(self):
        assert "low" in CONFIDENCE_LEVELS
        assert "medium" in CONFIDENCE_LEVELS
        assert "high" in CONFIDENCE_LEVELS
        assert "very_high" in CONFIDENCE_LEVELS


# ─── FeatureExtractor Tests ───────────────────────────────────────
class TestFeatureExtractor:
    def setup_method(self):
        self.extractor = FeatureExtractor()

    def test_extract_basic(self):
        content = "This is a test post about AI and technology."
        features = self.extractor.extract(content)
        assert features.word_count == 9
        assert features.sentence_count >= 1
        assert features.platform == ""

    def test_extract_empty(self):
        features = self.extractor.extract("")
        assert features.word_count == 0
        assert features.sentence_count == 0
        assert features.readability_estimate == 0.0

    def test_extract_hashtags(self):
        content = "Great post #AI #Tech #Future"
        features = self.extractor.extract(content)
        assert features.hashtag_count == 3

    def test_extract_mentions(self):
        content = "Thanks @user1 and @user2 for sharing"
        features = self.extractor.extract(content)
        assert features.mention_count == 2

    def test_extract_questions(self):
        content = "What do you think? Is AI the future? How will it change us?"
        features = self.extractor.extract(content)
        assert features.question_count == 3

    def test_extract_hook(self):
        content = "Did you know? AI is transforming everything."
        features = self.extractor.extract(content)
        assert features.has_hook is True

    def test_extract_no_hook(self):
        content = "This is a regular post about technology."
        features = self.extractor.extract(content)
        assert features.has_hook is False

    def test_extract_cta(self):
        content = "Great post! Comment below and share your thoughts."
        features = self.extractor.extract(content)
        assert features.has_cta is True

    def test_extract_no_cta(self):
        content = "Just a regular update about our company."
        features = self.extractor.extract(content)
        assert features.has_cta is False

    def test_extract_with_platform(self):
        features = self.extractor.extract("Test", platform="linkedin")
        assert features.platform == "linkedin"

    def test_extract_batch(self):
        contents = ["Post one", "Post two", "Post three"]
        features = self.extractor.extract_batch(contents, platform="x")
        assert len(features) == 3
        assert all(f.platform == "x" for f in features)

    def test_feature_vector(self):
        features = self.extractor.extract("Test content with #hashtags and @mentions")
        vec = self.extractor.to_feature_vector(features)
        assert len(vec) == 12
        assert all(isinstance(v, float) for v in vec)

    def test_to_dict(self):
        features = self.extractor.extract("Hello world")
        d = features.to_dict()
        assert "word_count" in d
        assert "has_hook" in d
        assert "platform" in d

    def test_urls_detected(self):
        content = "Check http://example.com and https://test.org"
        features = self.extractor.extract(content)
        assert features.url_count >= 1

    def test_emoji_count(self):
        content = "Great post! 🔥🔥🔥 Love it ❤️"
        features = self.extractor.extract(content)
        assert features.emoji_count >= 2


# ─── EngagementModel Tests ────────────────────────────────────────
class TestEngagementModel:
    def setup_method(self):
        self.model = EngagementModel()

    def test_predict_basic(self):
        features = ContentFeatures()
        features.word_count = 50
        features.has_hook = True
        features.has_cta = True
        features.readability_estimate = 0.8
        pred = self.model.predict(features, platform="facebook")
        assert pred.likes > 0
        assert pred.comments > 0
        assert pred.shares > 0
        assert pred.reach > 0
        assert pred.confidence > 0
        assert pred.prediction_id.startswith("ep_")

    def test_predict_empty_features(self):
        features = ContentFeatures()
        pred = self.model.predict(features)
        assert pred.likes >= 0
        assert pred.prediction_id.startswith("ep_")

    def test_predict_with_hook_bonus(self):
        features = ContentFeatures()
        features.word_count = 30
        features.has_hook = True
        features.has_cta = False
        pred_hook = self.model.predict(features, platform="facebook")
        features.has_hook = False
        pred_no_hook = self.model.predict(features, platform="facebook")
        assert pred_hook.likes >= pred_no_hook.likes

    def test_predict_with_cta_bonus(self):
        features = ContentFeatures()
        features.word_count = 30
        features.has_hook = False
        features.has_cta = True
        pred_cta = self.model.predict(features, platform="facebook")
        features.has_cta = False
        pred_no_cta = self.model.predict(features, platform="facebook")
        assert pred_cta.likes >= pred_no_cta.likes

    def test_predict_platforms(self):
        features = ContentFeatures()
        features.word_count = 40
        for platform in ("facebook", "instagram", "x", "linkedin", "tiktok"):
            pred = self.model.predict(features, platform=platform)
            assert pred.platform == platform
            assert pred.likes >= 0

    def test_predict_unknown_platform(self):
        features = ContentFeatures()
        features.word_count = 30
        pred = self.model.predict(features, platform="unknown_platform")
        assert pred.likes >= 0

    def test_predict_horizon_scaling(self):
        features = ContentFeatures()
        features.word_count = 30
        pred_24h = self.model.predict(features, horizon="24h")
        pred_7d = self.model.predict(features, horizon="7d")
        assert pred_7d.likes > pred_24h.likes

    def test_predict_audience_size(self):
        features = ContentFeatures()
        features.word_count = 30
        pred_small = self.model.predict(features, audience_size=100)
        pred_large = self.model.predict(features, audience_size=10000)
        assert pred_large.likes > pred_small.likes

    def test_engagement_rate_bounded(self):
        features = ContentFeatures()
        features.word_count = 50
        features.has_hook = True
        features.has_cta = True
        features.emoji_count = 10
        pred = self.model.predict(features, platform="tiktok")
        assert 0 <= pred.engagement_rate <= 1.0

    def test_predict_from_content(self):
        content = "Did you know? AI is changing everything! Comment below and share."
        pred = self.model.predict_from_content(content, platform="instagram")
        assert pred.likes > 0
        assert pred.platform == "instagram"

    def test_predict_from_content_empty(self):
        pred = self.model.predict_from_content("", platform="facebook")
        assert pred.prediction_id.startswith("ep_")
        assert pred.likes >= 0

    def test_to_dict(self):
        features = ContentFeatures()
        features.word_count = 20
        pred = self.model.predict(features, platform="x")
        d = pred.to_dict()
        assert "prediction_id" in d
        assert "likes" in d
        assert "confidence" in d
        assert "horizon" in d

    def test_impressions_greater_than_reach(self):
        features = ContentFeatures()
        features.word_count = 30
        pred = self.model.predict(features)
        assert pred.impressions >= pred.reach

    def test_ctr_bounded(self):
        features = ContentFeatures()
        features.word_count = 50
        pred = self.model.predict(features)
        assert 0 <= pred.ctr <= 1.0


# ─── ViralityEstimator Tests ──────────────────────────────────────
class TestViralityEstimator:
    def setup_method(self):
        self.estimator = ViralityEstimator()

    def test_estimate_basic(self):
        pred = EngagementPrediction()
        pred.likes = 100
        pred.comments = 20
        pred.shares = 15
        pred.saves = 10
        pred.reach = 500
        pred.engagement_rate = 0.08
        pred.confidence = 0.7
        est = self.estimator.estimate(pred, platform="facebook")
        assert est.virality_score > 0
        assert est.virality_probability > 0
        assert est.reach_multiplier >= 1.0
        assert est.estimate_id.startswith("ve_")

    def test_estimate_zero_engagement(self):
        pred = EngagementPrediction()
        pred.engagement_rate = 0.0
        est = self.estimator.estimate(pred)
        assert est.virality_score == 0.0

    def test_estimate_high_share_ratio(self):
        pred = EngagementPrediction()
        pred.likes = 50
        pred.shares = 20
        pred.comments = 5
        pred.saves = 5
        pred.reach = 500
        pred.engagement_rate = 0.1
        pred.confidence = 0.7
        est = self.estimator.estimate(pred)
        assert est.viral_trigger == "high_share_ratio"

    def test_estimate_high_discussion(self):
        pred = EngagementPrediction()
        pred.likes = 30
        pred.shares = 2
        pred.comments = 15
        pred.saves = 3
        pred.reach = 500
        pred.engagement_rate = 0.1
        pred.confidence = 0.7
        est = self.estimator.estimate(pred)
        assert est.viral_trigger == "high_discussion"

    def test_estimate_high_save_rate(self):
        pred = EngagementPrediction()
        pred.likes = 30
        pred.shares = 2
        pred.comments = 3
        pred.saves = 15
        pred.reach = 500
        pred.engagement_rate = 0.1
        pred.confidence = 0.7
        est = self.estimator.estimate(pred)
        assert est.viral_trigger == "high_save_rate"

    def test_viral_probability_bounded(self):
        pred = EngagementPrediction()
        pred.likes = 500
        pred.comments = 100
        pred.shares = 80
        pred.saves = 50
        pred.reach = 1000
        pred.engagement_rate = 0.3
        pred.confidence = 0.9
        est = self.estimator.estimate(pred)
        assert 0 <= est.virality_probability <= 0.95

    def test_risk_factor(self):
        pred = EngagementPrediction()
        pred.likes = 1000
        pred.comments = 200
        pred.shares = 100
        pred.saves = 50
        pred.reach = 1000
        pred.engagement_rate = 0.5
        pred.confidence = 0.8
        est = self.estimator.estimate(pred)
        assert 0 <= est.risk_factor <= 1.0

    def test_to_dict(self):
        pred = EngagementPrediction()
        pred.likes = 50
        pred.comments = 10
        pred.shares = 5
        pred.reach = 300
        pred.engagement_rate = 0.05
        pred.confidence = 0.6
        est = self.estimator.estimate(pred)
        d = est.to_dict()
        assert "estimate_id" in d
        assert "virality_score" in d
        assert "reach_multiplier" in d

    def test_quick_viral_score(self):
        score = self.estimator.estimate_viral_score(100, audience_size=1000)
        assert 0 <= score <= 1.0

    def test_quick_viral_score_zero_audience(self):
        score = self.estimator.estimate_viral_score(100, audience_size=0)
        assert score == 0.0

    def test_viral_threshold(self):
        assert self.estimator.get_viral_threshold("tiktok") == 0.3
        assert self.estimator.get_viral_threshold("linkedin") == 0.3
        assert self.estimator.get_viral_threshold("unknown") == 0.3


# ─── TimingOptimizer Tests ────────────────────────────────────────
class TestTimingOptimizer:
    def setup_method(self):
        self.optimizer = TimingOptimizer()

    def test_predict_best_times(self):
        slots = self.optimizer.predict_best_times(platform="facebook", count=3)
        assert len(slots) <= 3
        assert len(slots) > 0
        assert all(isinstance(s, TimeSlot) for s in slots)

    def test_predict_best_times_sorted_by_score(self):
        slots = self.optimizer.predict_best_times(platform="instagram", count=5)
        scores = [s.score for s in slots]
        assert scores == sorted(scores, reverse=True)

    def test_predict_for_content_reel(self):
        slots = self.optimizer.predict_for_content(platform="tiktok", content_type="reel", count=3)
        assert len(slots) > 0

    def test_predict_for_content_article(self):
        slots = self.optimizer.predict_for_content(platform="medium", content_type="article", count=3)
        assert len(slots) > 0

    def test_custom_peaks(self):
        self.optimizer.set_custom_peaks("facebook", [3, 6, 9])
        slots = self.optimizer.predict_best_times(platform="facebook", count=3)
        hours = [s.hour for s in slots]
        assert 3 in hours or 6 in hours or 9 in hours

    def test_score_hour_peak(self):
        score = self.optimizer.score_hour(9, platform="facebook")
        assert score == 0.9

    def test_score_hour_adjacent(self):
        score = self.optimizer.score_hour(10, platform="facebook")
        assert score >= 0.7

    def test_score_hour_off_peak(self):
        score = self.optimizer.score_hour(3, platform="facebook")
        assert score <= 0.5

    def test_default_platforms(self):
        for platform in ("facebook", "instagram", "x", "linkedin", "youtube", "tiktok"):
            slots = self.optimizer.predict_best_times(platform=platform, count=2)
            assert len(slots) > 0

    def test_to_dict(self):
        slots = self.optimizer.predict_best_times(platform="x", count=1)
        if slots:
            d = slots[0].to_dict()
            assert "slot_id" in d
            assert "hour" in d
            assert "score" in d

    def test_unknown_platform(self):
        slots = self.optimizer.predict_best_times(platform="unknown", count=3)
        assert len(slots) > 0


# ─── AudiencePredictor Tests ──────────────────────────────────────
class TestAudiencePredictor:
    def setup_method(self):
        self.predictor = AudiencePredictor()

    def test_predict_facebook(self):
        pred = EngagementPrediction()
        pred.likes = 50
        pred.comments = 10
        pred.reach = 500
        pred.engagement_rate = 0.08
        pred.confidence = 0.7
        result = self.predictor.predict(pred, platform="facebook", audience_size=1000)
        assert len(result.segments) > 0
        assert result.primary_segment != ""
        assert result.total_reach == 500
        assert result.prediction_id.startswith("ap_")

    def test_predict_instagram(self):
        pred = EngagementPrediction()
        pred.likes = 80
        pred.reach = 400
        pred.engagement_rate = 0.1
        pred.confidence = 0.7
        result = self.predictor.predict(pred, platform="instagram", audience_size=500)
        assert len(result.segments) > 0

    def test_predict_x(self):
        pred = EngagementPrediction()
        pred.likes = 20
        pred.reach = 600
        pred.engagement_rate = 0.05
        pred.confidence = 0.6
        result = self.predictor.predict(pred, platform="x")
        assert len(result.segments) > 0

    def test_predict_linkedin(self):
        pred = EngagementPrediction()
        pred.likes = 30
        pred.reach = 300
        pred.engagement_rate = 0.06
        pred.confidence = 0.7
        result = self.predictor.predict(pred, platform="linkedin")
        assert len(result.segments) > 0

    def test_predict_unknown_platform(self):
        pred = EngagementPrediction()
        pred.likes = 10
        pred.reach = 100
        pred.engagement_rate = 0.05
        pred.confidence = 0.5
        result = self.predictor.predict(pred, platform="unknown")
        assert len(result.segments) > 0

    def test_segment_estimated_size(self):
        pred = EngagementPrediction()
        pred.likes = 50
        pred.reach = 500
        pred.engagement_rate = 0.08
        pred.confidence = 0.7
        result = self.predictor.predict(pred, platform="facebook", audience_size=1000)
        total_size = sum(s.estimated_size for s in result.segments)
        assert total_size == 1000

    def test_segment_count(self):
        count = self.predictor.get_segment_count("facebook")
        assert count == 4

    def test_to_dict(self):
        pred = EngagementPrediction()
        pred.likes = 50
        pred.reach = 500
        pred.engagement_rate = 0.08
        pred.confidence = 0.7
        result = self.predictor.predict(pred, platform="linkedin")
        d = result.to_dict()
        assert "segments" in d
        assert "total_reach" in d
        assert "primary_segment" in d

    def test_primary_segment(self):
        pred = EngagementPrediction()
        pred.likes = 50
        pred.reach = 500
        pred.engagement_rate = 0.08
        pred.confidence = 0.7
        result = self.predictor.predict(pred, platform="facebook", audience_size=1000)
        max_weight_seg = max(result.segments, key=lambda s: s.engagement_weight)
        assert result.primary_segment == max_weight_seg.name


# ─── PredictionMemory Tests ───────────────────────────────────────
class TestPredictionMemory:
    def setup_method(self):
        self.memory = PredictionMemory()

    def test_store(self):
        record = self.memory.store("c1", {"likes": 50, "comments": 10}, platform="facebook")
        assert record.record_id.startswith("pr_")
        assert record.content_id == "c1"
        assert record.predicted["likes"] == 50

    def test_store_multiple(self):
        self.memory.store("c1", {"likes": 50})
        self.memory.store("c2", {"likes": 30})
        assert self.memory.record_count == 2

    def test_record_actual(self):
        record = self.memory.store("c1", {"likes": 50, "comments": 10})
        updated = self.memory.record_actual(record.record_id, {"likes": 60, "comments": 15})
        assert updated is not None
        assert updated.actual["likes"] == 60
        assert updated.compared is True

    def test_record_actual_not_found(self):
        result = self.memory.record_actual("nonexistent", {"likes": 10})
        assert result is None

    def test_record_actual_by_content(self):
        record = self.memory.store("c1", {"likes": 50})
        updated = self.memory.record_actual_by_content("c1", {"likes": 55})
        assert updated is not None
        assert updated.actual["likes"] == 55

    def test_record_actual_by_content_not_found(self):
        result = self.memory.record_actual_by_content("nonexistent", {"likes": 10})
        assert result is None

    def test_get_comparisons(self):
        r1 = self.memory.store("c1", {"likes": 50}, platform="facebook")
        r2 = self.memory.store("c2", {"likes": 30}, platform="facebook")
        self.memory.record_actual(r1.record_id, {"likes": 55})
        self.memory.record_actual(r2.record_id, {"likes": 25})
        comparisons = self.memory.get_comparisons(platform="facebook")
        assert len(comparisons) == 2

    def test_get_comparisons_filtered(self):
        r1 = self.memory.store("c1", {"likes": 50}, platform="facebook")
        r2 = self.memory.store("c2", {"likes": 30}, platform="x")
        self.memory.record_actual(r1.record_id, {"likes": 55})
        self.memory.record_actual(r2.record_id, {"likes": 25})
        comparisons = self.memory.get_comparisons(platform="facebook")
        assert len(comparisons) == 1

    def test_get_uncompared(self):
        self.memory.store("c1", {"likes": 50})
        self.memory.store("c2", {"likes": 30})
        uncompared = self.memory.get_uncompared()
        assert len(uncompared) == 2

    def test_compute_accuracy(self):
        r = self.memory.store("c1", {"likes": 100})
        self.memory.record_actual(r.record_id, {"likes": 110})
        accuracy = self.memory.compute_accuracy()
        assert accuracy["count"] == 1
        assert accuracy["accuracy"] > 0

    def test_compute_accuracy_empty(self):
        accuracy = self.memory.compute_accuracy()
        assert accuracy["count"] == 0

    def test_to_dict(self):
        record = self.memory.store("c1", {"likes": 50})
        d = record.to_dict()
        assert "record_id" in d
        assert "content_id" in d

    def test_stats(self):
        self.memory.store("c1", {"likes": 50})
        self.memory.store("c2", {"likes": 30})
        stats = self.memory.get_stats()
        assert stats["total"] == 2
        assert stats["compared"] == 0
        assert stats["uncompared"] == 2

    def test_max_entries(self):
        mem = PredictionMemory(max_entries=3)
        mem.store("c1", {"likes": 10})
        mem.store("c2", {"likes": 20})
        mem.store("c3", {"likes": 30})
        mem.store("c4", {"likes": 40})
        assert mem.record_count == 3


# ─── PredictionMetrics Tests ──────────────────────────────────────
class TestPredictionMetrics:
    def setup_method(self):
        self.metrics = PredictionMetrics()

    def test_record_prediction(self):
        self.metrics.record_prediction(confidence=0.8)
        assert self.metrics._total_predictions == 1

    def test_record_comparison(self):
        self.metrics.record_comparison(predicted=100, actual=110)
        assert self.metrics._total_comparisons == 1

    def test_mae(self):
        self.metrics.record_comparison(100, 110)
        self.metrics.record_comparison(200, 180)
        mae = self.metrics.get_mae()
        assert mae > 0

    def test_mae_empty(self):
        assert self.metrics.get_mae() == 0.0

    def test_rmse(self):
        self.metrics.record_comparison(100, 110)
        rmse = self.metrics.get_rmse()
        assert rmse > 0

    def test_rmse_empty(self):
        assert self.metrics.get_rmse() == 0.0

    def test_direction_accuracy(self):
        self.metrics.record_comparison(100, 110, predicted_direction=1, actual_direction=1)
        self.metrics.record_comparison(200, 190, predicted_direction=-1, actual_direction=-1)
        assert self.metrics.get_direction_accuracy() == 1.0

    def test_direction_accuracy_partial(self):
        self.metrics.record_comparison(100, 110, predicted_direction=1, actual_direction=1)
        self.metrics.record_comparison(200, 190, predicted_direction=1, actual_direction=-1)
        assert self.metrics.get_direction_accuracy() == 0.5

    def test_calibration_score(self):
        self.metrics.record_prediction(0.8)
        self.metrics.record_comparison(100, 105, confidence=0.8)
        score = self.metrics.get_calibration_score()
        assert score > 0

    def test_summary(self):
        self.metrics.record_prediction(0.7)
        self.metrics.record_comparison(100, 110)
        summary = self.metrics.get_summary()
        assert "mae" in summary
        assert "rmse" in summary
        assert "total_predictions" in summary

    def test_reset(self):
        self.metrics.record_prediction(0.7)
        self.metrics.record_comparison(100, 110)
        self.metrics.reset()
        assert self.metrics._total_predictions == 0
        assert self.metrics._total_comparisons == 0


# ─── PredictionValidator Tests ────────────────────────────────────
class TestPredictionValidator:
    def setup_method(self):
        self.validator = PredictionValidator()

    def test_validate_good(self):
        pred = EngagementPrediction()
        pred.likes = 50
        pred.comments = 10
        pred.reach = 500
        pred.engagement_rate = 0.08
        pred.confidence = 0.7
        result = self.validator.validate(pred, platform="facebook")
        assert result.is_valid is True
        assert result.quality_score > 0

    def test_validate_low_confidence(self):
        pred = EngagementPrediction()
        pred.confidence = 0.1
        pred.reach = 100
        pred.engagement_rate = 0.05
        result = self.validator.validate(pred)
        assert len(result.warnings) > 0

    def test_validate_negative_likes(self):
        pred = EngagementPrediction()
        pred.likes = -10
        pred.reach = 100
        pred.engagement_rate = 0.05
        result = self.validator.validate(pred)
        assert result.is_valid is False
        assert any("Negative likes" in i for i in result.issues)

    def test_validate_high_engagement_rate(self):
        pred = EngagementPrediction()
        pred.engagement_rate = 1.5
        pred.reach = 100
        result = self.validator.validate(pred)
        assert result.is_valid is False

    def test_validate_high_engagement_ratio(self):
        pred = EngagementPrediction()
        pred.likes = 400
        pred.comments = 50
        pred.shares = 30
        pred.reach = 100
        pred.engagement_rate = 0.1
        pred.confidence = 0.7
        result = self.validator.validate(pred)
        assert any("high engagement-to-reach" in w for w in result.warnings)

    def test_validate_confidence_levels(self):
        pred = EngagementPrediction()
        pred.reach = 100
        pred.engagement_rate = 0.05

        pred.confidence = 0.9
        result = self.validator.validate(pred)
        assert result.confidence_level == "high"

        pred.confidence = 0.6
        result = self.validator.validate(pred)
        assert result.confidence_level == "medium"

        pred.confidence = 0.2
        result = self.validator.validate(pred)
        assert result.confidence_level == "low"

    def test_set_min_confidence(self):
        self.validator.set_min_confidence(0.8)
        assert self.validator._min_confidence == 0.8

    def test_set_drift_threshold(self):
        self.validator.set_drift_threshold(0.5)
        assert self.validator._drift_threshold == 0.5

    def test_to_dict(self):
        pred = EngagementPrediction()
        pred.reach = 100
        pred.engagement_rate = 0.05
        result = self.validator.validate(pred)
        d = result.to_dict()
        assert "is_valid" in d
        assert "quality_score" in d
        assert "confidence_level" in d

    def test_drift_detection_with_memory(self):
        memory = PredictionMemory()
        for i in range(10):
            r = memory.store(f"c{i}", {"likes": 100, "comments": 20, "shares": 10}, platform="facebook")
            memory.record_actual(r.record_id, {"likes": 200, "comments": 40, "shares": 20})
        validator = PredictionValidator(memory=memory)
        validator.set_drift_threshold(0.1)
        pred = EngagementPrediction()
        pred.likes = 500
        pred.comments = 100
        pred.shares = 50
        pred.reach = 500
        pred.engagement_rate = 0.5
        pred.confidence = 0.3
        result = validator.validate(pred, platform="facebook")
        assert result.drift_detected is True

    def test_no_drift_with_insufficient_data(self):
        memory = PredictionMemory()
        validator = PredictionValidator(memory=memory)
        pred = EngagementPrediction()
        pred.likes = 50
        pred.reach = 500
        pred.engagement_rate = 0.08
        pred.confidence = 0.7
        result = validator.validate(pred)
        assert result.drift_detected is False


# ─── EngagementManager Tests ──────────────────────────────────────
class TestEngagementManager:
    def setup_method(self):
        self.manager = EngagementManager()

    def test_predict_basic(self):
        content = "Did you know? AI is transforming the world! Comment below."
        report = self.manager.predict(content, platform="facebook")
        assert report.prediction is not None
        assert report.prediction.likes > 0
        assert report.virality is not None
        assert report.timing is not None
        assert report.audience is not None
        assert report.validation is not None
        assert report.report_id.startswith("er_")

    def test_predict_with_profile(self):
        profile = PredictionProfile(horizon="7d", platform="linkedin", content_type="article")
        content = "Professional insights on AI transformation in enterprise."
        report = self.manager.predict(content, profile=profile)
        assert report.prediction.horizon == "7d"
        assert report.prediction.platform == "linkedin"

    def test_predict_empty_content(self):
        report = self.manager.predict("", platform="x")
        assert report.prediction is not None
        assert report.prediction.prediction_id.startswith("ep_")

    def test_predict_virality_disabled(self):
        profile = PredictionProfile()
        profile.include_virality = False
        report = self.manager.predict("Test content", profile=profile)
        assert report.virality is None

    def test_predict_timing_disabled(self):
        profile = PredictionProfile()
        profile.include_timing = False
        report = self.manager.predict("Test content", profile=profile)
        assert report.timing is None

    def test_predict_audience_disabled(self):
        profile = PredictionProfile()
        profile.include_audience = False
        report = self.manager.predict("Test content", profile=profile)
        assert report.audience is None

    def test_record_actual(self):
        report = self.manager.predict("Test content about AI", platform="facebook")
        success = self.manager.record_actual(
            report.report_id,
            {"likes": 60, "comments": 12, "shares": 8, "reach": 550},
        )
        assert success is True

    def test_record_actual_not_found(self):
        success = self.manager.record_actual("nonexistent", {"likes": 10})
        assert success is False

    def test_health(self):
        self.manager.predict("Test content", platform="facebook")
        health = self.manager.get_health()
        assert health["total_reports"] == 1
        assert "memory_stats" in health
        assert "metrics" in health

    def test_recent_reports(self):
        for i in range(3):
            self.manager.predict(f"Content {i}")
        reports = self.manager.get_recent_reports(2)
        assert len(reports) == 2

    def test_events(self):
        self.manager.predict("Test content")
        assert len(self.manager.events) == 1
        assert self.manager.events[0]["event"] == "engagement_predicted"

    def test_prediction_count(self):
        assert self.manager.prediction_count == 0
        self.manager.predict("Content 1")
        self.manager.predict("Content 2")
        assert self.manager.prediction_count == 2

    def test_to_dict(self):
        report = self.manager.predict("Test", platform="x")
        d = report.to_dict()
        assert "report_id" in d
        assert "prediction" in d
        assert "virality" in d
        assert "timing" in d
        assert "audience" in d
        assert "validation" in d

    def test_all_platforms(self):
        for platform in ("facebook", "instagram", "x", "linkedin", "youtube", "tiktok"):
            report = self.manager.predict(f"Test content for {platform}", platform=platform)
            assert report.prediction.platform == platform

    def test_metrics_tracking(self):
        self.manager.predict("Test 1", platform="facebook")
        self.manager.predict("Test 2", platform="x")
        assert self.manager.metrics._total_predictions == 2

    def test_memory_stores_predictions(self):
        self.manager.predict("Test content")
        assert self.manager.memory.record_count >= 1


# ─── Exceptions Tests ─────────────────────────────────────────────
class TestExceptions:
    def test_base_exception(self):
        with raise_ctx(EngagementPredictionError("test")):
            raise EngagementPredictionError("test")

    def test_feature_extraction_error(self):
        with raise_ctx(FeatureExtractionError("test")):
            raise FeatureExtractionError("test")

    def test_prediction_error(self):
        with raise_ctx(PredictionError("test")):
            raise PredictionError("test")

    def test_validation_error(self):
        with raise_ctx(ValidationError("test")):
            raise ValidationError("test")

    def test_inheritance(self):
        assert issubclass(FeatureExtractionError, EngagementPredictionError)
        assert issubclass(PredictionError, EngagementPredictionError)
        assert issubclass(ValidationError, EngagementPredictionError)


# ─── Integration Tests ────────────────────────────────────────────
class TestEngagementPredictorIntegration:
    def setup_method(self):
        self.manager = EngagementManager()

    def test_full_pipeline(self):
        content = (
            "Did you know? AI is transforming every industry! "
            "Here's the thing — 85% of companies will adopt AI by 2027. "
            "What do you think? Comment below and share your experience. "
            "#AI #Future #Technology"
        )
        profile = PredictionProfile(horizon="24h", platform="linkedin", content_type="article")
        report = self.manager.predict(content, profile=profile, audience_size=5000)

        assert report.prediction is not None
        assert report.prediction.likes > 0
        assert report.prediction.confidence > 0
        assert report.virality is not None
        assert report.timing is not None
        assert len(report.timing) > 0
        assert report.audience is not None
        assert len(report.audience.segments) > 0
        assert report.validation is not None
        assert report.validation.is_valid is True

    def test_cross_platform_comparison(self):
        content = "Great product launch! Check out our new features. #Launch #Product"
        platforms = ["facebook", "instagram", "linkedin", "x"]
        predictions = {}
        for platform in platforms:
            report = self.manager.predict(content, platform=platform)
            predictions[platform] = report.prediction.to_dict()

        platforms_sorted = sorted(platforms, key=lambda p: predictions[p]["likes"], reverse=True)
        assert len(platforms_sorted) == 4

    def test_prediction_then_actual(self):
        content = "Amazing content about sustainable energy! #GreenEnergy"
        report = self.manager.predict(content, platform="instagram")
        report_id = report.report_id
        pred = report.prediction

        actual = {
            "likes": pred.likes * 1.1,
            "comments": pred.comments * 0.9,
            "shares": pred.shares * 1.2,
            "reach": pred.reach * 0.95,
        }
        success = self.manager.record_actual(report_id, actual)
        assert success is True

        accuracy = self.manager.memory.compute_accuracy(platform="instagram")
        assert accuracy["count"] >= 1

    def test_virality_pipeline(self):
        content = "This is going viral! Share with everyone! #Viral"
        report = self.manager.predict(content, platform="tiktok")
        assert report.virality is not None
        assert report.virality.virality_score >= 0
        assert report.virality.reach_multiplier >= 1.0

    def test_timing_pipeline(self):
        content = "Morning coffee and AI news. ☕🤖"
        report = self.manager.predict(content, platform="twitter")
        assert report.timing is not None
        assert len(report.timing) > 0
        best_time = report.timing[0]
        assert best_time.score > 0

    def test_multiple_optimizations(self):
        contents = [
            "Post about technology trends",
            "Industry insights on AI adoption",
            "Quick tip for productivity",
        ]
        for content in contents:
            self.manager.predict(content, platform="facebook")
        assert self.manager.prediction_count == 3
        assert len(self.manager.events) == 3
class raise_ctx:
    def __init__(self, exc):
        self.exc = exc
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        assert exc_type is type(self.exc)
        assert str(exc_val) == str(self.exc)
        return True
