"""Tests for Layer 9 Module 7 — Quality Calibration Engine."""
from layers.layer09_learning.modules.quality_calibration.calibration_profile import (
    CalibrationProfile,
)
from layers.layer09_learning.modules.quality_calibration.threshold_manager import (
    ThresholdManager, ThresholdConfig,
)
from layers.layer09_learning.modules.quality_calibration.score_adjuster import (
    ScoreAdjuster,
)
from layers.layer09_learning.modules.quality_calibration.confidence_calibrator import (
    ConfidenceCalibrator,
)
from layers.layer09_learning.modules.quality_calibration.evaluator import Evaluator
from layers.layer09_learning.modules.quality_calibration.benchmark_manager import (
    BenchmarkManager,
)
from layers.layer09_learning.modules.quality_calibration.calibration_history import (
    CalibrationHistory,
)
from layers.layer09_learning.modules.quality_calibration.calibration_metrics import CalibrationMetrics
from layers.layer09_learning.modules.quality_calibration.calibration_validator import (
    CalibrationValidator,
)
from layers.layer09_learning.modules.quality_calibration.calibration_manager import (
    CalibrationManager, CalibrationCycleResult,
)
from layers.layer09_learning.modules.quality_calibration.exceptions import (
    CalibrationError, ThresholdError, BenchmarkError, ValidationError,
)


# ─── CalibrationProfile Tests ────────────────────────────────────────
class TestCalibrationProfile:
    def test_create(self):
        p = CalibrationProfile("engagement", "engagement")
        assert p.profile_id.startswith("cp_")
        assert p.metric_name == "engagement"
        assert p.status == "pending"

    def test_create_invalid_type(self):
        p = CalibrationProfile("test", "invalid")
        assert p.metric_type == "quality"

    def test_update(self):
        p = CalibrationProfile("test")
        p.update(0.5, 0.7)
        assert p.bias == 0.2
        assert p.status == "calibrated"
        assert p.calibration_count == 1

    def test_calibration_accuracy(self):
        p = CalibrationProfile("test")
        p.calibration_count = 10
        assert p.calibration_accuracy > 0

    def test_calibration_accuracy_zero(self):
        assert CalibrationProfile().calibration_accuracy == 0.0

    def test_is_stale(self):
        p = CalibrationProfile("test")
        assert p.is_stale is True

    def test_to_dict(self):
        p = CalibrationProfile("engagement", "engagement")
        d = p.to_dict()
        assert "profile_id" in d
        assert d["metric_name"] == "engagement"


# ─── ThresholdConfig Tests ────────────────────────────────────────────
class TestThresholdConfig:
    def test_create(self):
        t = ThresholdConfig("blog", "quality")
        assert t.context == "blog"
        assert t.min_threshold == 0.3
        assert t.hard_stop is False

    def test_to_dict(self):
        t = ThresholdConfig("x", "safety")
        d = t.to_dict()
        assert d["context"] == "x"
        assert d["hard_stop"] is False


# ─── ThresholdManager Tests ──────────────────────────────────────────
class TestThresholdManager:
    def setup_method(self):
        self.manager = ThresholdManager()

    def test_get_default(self):
        config = self.manager.get_threshold("quality")
        assert config.min_threshold == 0.3

    def test_set_threshold(self):
        config = ThresholdConfig("test", "custom")
        config.min_threshold = 0.5
        self.manager.set_threshold(config)
        result = self.manager.get_threshold("custom")
        assert result.min_threshold == 0.5

    def test_set_context(self):
        config = ThresholdConfig("blog", "quality")
        config.min_threshold = 0.7
        self.manager.set_context_threshold("blog", config)
        result = self.manager.get_threshold("quality", "blog")
        assert result.min_threshold == 0.7

    def test_evaluate_pass(self):
        result = self.manager.evaluate("quality", 0.8)
        assert result["status"] in ("pass", "excellent")

    def test_evaluate_fail(self):
        result = self.manager.evaluate("quality", 0.1)
        assert result["status"] == "fail"

    def test_evaluate_warning(self):
        result = self.manager.evaluate("quality", 0.45)
        assert result["status"] == "warning"

    def test_evaluate_hard_stop(self):
        config = ThresholdConfig("test", "safety")
        config.min_threshold = 0.5
        config.hard_stop = True
        self.manager.set_threshold(config)
        result = self.manager.evaluate("safety", 0.1)
        assert result["status"] == "hard_stop"

    def test_evaluate_excellent(self):
        result = self.manager.evaluate("quality", 0.9)
        assert result["status"] == "excellent"


# ─── ScoreAdjuster Tests ─────────────────────────────────────────────
class TestScoreAdjuster:
    def setup_method(self):
        self.adjuster = ScoreAdjuster()

    def test_set_bias(self):
        self.adjuster.set_bias("quality", -0.1, 0.8)
        assert self.adjuster.get_bias("quality") == -0.1

    def test_adjust(self):
        self.adjuster.set_bias("quality", -0.1, 0.8)
        result = self.adjuster.adjust("quality", 0.7)
        assert result.original_score == 0.7
        assert result.adjusted_score != 0.7

    def test_adjust_no_bias(self):
        result = self.adjuster.adjust("unknown", 0.5)
        assert result.adjusted_score == 0.5

    def test_adjust_clamped(self):
        self.adjuster.set_bias("quality", 0.5, 1.0)
        result = self.adjuster.adjust("quality", 0.9)
        assert result.adjusted_score <= 1.0

    def test_adjust_batch(self):
        self.adjuster.set_bias("a", -0.1, 0.8)
        results = self.adjuster.adjust_batch({"a": 0.7, "b": 0.5})
        assert len(results) == 2

    def test_get_biases(self):
        self.adjuster.set_bias("a", 0.1)
        self.adjuster.set_bias("b", -0.1)
        biases = self.adjuster.get_biases()
        assert "a" in biases
        assert "b" in biases

    def test_result_to_dict(self):
        self.adjuster.set_bias("q", -0.05, 0.9)
        result = self.adjuster.adjust("q", 0.8)
        d = result.to_dict()
        assert "original_score" in d
        assert "adjusted_score" in d


# ─── ConfidenceCalibrator Tests ──────────────────────────────────────
class TestConfidenceCalibrator:
    def setup_method(self):
        self.calibrator = ConfidenceCalibrator()

    def test_calibrate_basic(self):
        predictions = [
            {"confidence": 0.9, "correct": True},
            {"confidence": 0.9, "correct": True},
            {"confidence": 0.3, "correct": False},
            {"confidence": 0.3, "correct": False},
        ]
        bins = self.calibrator.calibrate(predictions)
        assert len(bins) >= 1

    def test_calibrate_empty(self):
        bins = self.calibrator.calibrate([])
        assert len(bins) == 0

    def test_get_overall_ece(self):
        predictions = [
            {"confidence": 0.8, "correct": True},
            {"confidence": 0.2, "correct": False},
        ]
        self.calibrator.calibrate(predictions)
        ece = self.calibrator.get_overall_ece()
        assert ece >= 0

    def test_calibration_count(self):
        self.calibrator.calibrate([])
        self.calibrator.calibrate([])
        assert self.calibrator.calibration_count == 2

    def test_bins_to_dict(self):
        predictions = [{"confidence": 0.8, "correct": True}, {"confidence": 0.3, "correct": False}]
        bins = self.calibrator.calibrate(predictions)
        if bins:
            d = bins[0].to_dict()
            assert "bin_label" in d


# ─── Evaluator Tests ─────────────────────────────────────────────────
class TestEvaluator:
    def setup_method(self):
        self.evaluator = Evaluator()

    def test_evaluate_accurate(self):
        predicted = {"engagement": 0.8}
        actual = {"engagement": 0.82}
        results = self.evaluator.evaluate(predicted, actual)
        assert len(results) == 1
        assert results[0].direction == "accurate"

    def test_evaluate_underpredicted(self):
        predicted = {"engagement": 0.5}
        actual = {"engagement": 0.8}
        results = self.evaluator.evaluate(predicted, actual)
        assert results[0].direction == "underpredicted"

    def test_evaluate_overpredicted(self):
        predicted = {"engagement": 0.9}
        actual = {"engagement": 0.5}
        results = self.evaluator.evaluate(predicted, actual)
        assert results[0].direction == "overpredicted"

    def test_mae(self):
        predicted = {"a": 0.5, "b": 0.8}
        actual = {"a": 0.6, "b": 0.7}
        self.evaluator.evaluate(predicted, actual)
        mae = self.evaluator.get_mae()
        assert mae == 0.1

    def test_rmse(self):
        self.evaluator.evaluate({"a": 0.5}, {"a": 0.7})
        rmse = self.evaluator.get_rmse()
        assert rmse > 0

    def test_direction_summary(self):
        self.evaluator.evaluate({"a": 0.5}, {"a": 0.8})
        self.evaluator.evaluate({"b": 0.9}, {"b": 0.5})
        summary = self.evaluator.get_direction_summary()
        assert summary.get("underpredicted", 0) >= 1

    def test_empty(self):
        assert self.evaluator.get_mae() == 0.0


# ─── BenchmarkManager Tests ──────────────────────────────────────────
class TestBenchmarkManager:
    def setup_method(self):
        self.manager = BenchmarkManager()

    def test_create_run(self):
        run = self.manager.create_run("v1", {"engagement": 0.8, "reach": 0.6})
        assert run.run_id.startswith("bch_")
        assert self.manager.run_count == 1

    def test_get_latest(self):
        self.manager.create_run("test", {"a": 0.5})
        self.manager.create_run("test", {"a": 0.8})
        latest = self.manager.get_latest("test")
        assert latest.scores["a"] == 0.8

    def test_compare_runs(self):
        self.manager.create_run("test", {"a": 0.5})
        self.manager.create_run("test", {"a": 0.8})
        self.manager.create_run("other", {"a": 0.3})
        runs = self.manager.compare_runs("test", 2)
        assert len(runs) == 2

    def test_get_improvement(self):
        self.manager.create_run("test", {"a": 0.5})
        self.manager.create_run("test", {"a": 0.8})
        improvement = self.manager.get_improvement("test")
        assert improvement > 0

    def test_get_best_run(self):
        self.manager.create_run("test", {"a": 0.5})
        self.manager.create_run("test", {"a": 0.9})
        best = self.manager.get_best_run("test")
        assert best.scores["a"] == 0.9

    def test_get_all_names(self):
        self.manager.create_run("a", {"x": 0.5})
        self.manager.create_run("b", {"y": 0.6})
        names = self.manager.get_all_names()
        assert "a" in names

    def test_run_to_dict(self):
        run = self.manager.create_run("test", {"a": 0.8}, 150.0)
        d = run.to_dict()
        assert "run_id" in d
        assert d["duration_ms"] == 150.0


# ─── CalibrationHistory Tests ────────────────────────────────────────
class TestCalibrationHistory:
    def setup_method(self):
        self.history = CalibrationHistory()

    def test_record(self):
        entry = self.history.record("quality", 0.1, 0.05, trigger="auto")
        assert entry.metric == "quality"
        assert entry.bias_change == -0.05

    def test_get_metric_history(self):
        self.history.record("a", 0.1, 0.05)
        self.history.record("b", 0.2, 0.1)
        assert len(self.history.get_metric_history("a")) == 1

    def test_get_recent(self):
        for _ in range(5):
            self.history.record("a", 0.1, 0.05)
        assert len(self.history.get_recent(3)) == 3

    def test_get_by_trigger(self):
        self.history.record("a", 0.1, 0.05, trigger="manual")
        self.history.record("a", 0.1, 0.05, trigger="auto")
        assert len(self.history.get_by_trigger("manual")) == 1

    def test_get_latest(self):
        self.history.record("a", 0.1, 0.05)
        self.history.record("a", 0.05, 0.02)
        latest = self.history.get_latest("a")
        assert latest.new_bias == 0.02

    def test_entry_to_dict(self):
        entry = self.history.record("q", 0.1, 0.05)
        d = entry.to_dict()
        assert "bias_change" in d


# ─── CalibrationMetrics Tests ────────────────────────────────────────
class TestCalibrationMetrics:
    def setup_method(self):
        self.metrics = CalibrationMetrics()

    def test_record_calibration(self):
        self.metrics.record_calibration(0.05)
        assert self.metrics.get_avg_ece() == 0.05

    def test_record_evaluation(self):
        self.metrics.record_evaluation(0.1)
        assert self.metrics.get_avg_mae() == 0.1

    def test_record_adjustment(self):
        self.metrics.record_adjustment()
        assert self.metrics.get_summary()["total_adjustments"] == 1

    def test_record_benchmark(self):
        self.metrics.record_benchmark()
        assert self.metrics.get_summary()["total_benchmarks"] == 1

    def test_summary(self):
        self.metrics.record_calibration(0.05)
        self.metrics.record_evaluation(0.1)
        summary = self.metrics.get_summary()
        assert "total_calibrations" in summary

    def test_reset(self):
        self.metrics.record_calibration(0.1)
        self.metrics.reset()
        assert self.metrics.get_avg_ece() == 0.0


# ─── CalibrationValidator Tests ──────────────────────────────────────
class TestCalibrationValidator:
    def setup_method(self):
        self.validator = CalibrationValidator()

    def test_validate_good(self):
        result = self.validator.validate({"q": 0.05}, {"q": 20}, ece=0.05)
        assert result.is_valid is True

    def test_validate_high_bias(self):
        result = self.validator.validate({"q": 0.6})
        assert result.is_valid is False

    def test_validate_low_samples(self):
        result = self.validator.validate({"q": 0.1}, {"q": 5})
        assert len(result.warnings) >= 1

    def test_validate_high_ece(self):
        result = self.validator.validate({}, ece=0.3)
        assert result.is_valid is False

    def test_validate_warning_bias(self):
        result = self.validator.validate({"q": 0.35})
        assert len(result.warnings) >= 1

    def test_result_to_dict(self):
        result = self.validator.validate({"q": 0.05})
        d = result.to_dict()
        assert "is_valid" in d
        assert "score" in d


# ─── CalibrationCycleResult Tests ────────────────────────────────────
class TestCalibrationCycleResult:
    def test_create(self):
        r = CalibrationCycleResult()
        assert r.cycle_id.startswith("ccy_")

    def test_to_dict(self):
        r = CalibrationCycleResult()
        r.metrics_calibrated = 5
        d = r.to_dict()
        assert d["metrics_calibrated"] == 5


# ─── CalibrationManager Tests ────────────────────────────────────────
class TestCalibrationManager:
    def setup_method(self):
        self.manager = CalibrationManager()

    def test_run_calibration_cycle(self):
        predicted = {"engagement": 0.5, "quality": 0.7}
        actual = {"engagement": 0.7, "quality": 0.6}
        result = self.manager.run_calibration_cycle(predicted, actual)
        assert result.cycle_id.startswith("ccy_")
        assert result.metrics_calibrated == 2

    def test_run_cycle_with_confidence(self):
        predicted = {"engagement": 0.5}
        actual = {"engagement": 0.7}
        conf = [
            {"confidence": 0.8, "correct": True},
            {"confidence": 0.3, "correct": False},
        ]
        result = self.manager.run_calibration_cycle(predicted, actual, conf)
        assert result.ece >= 0

    def test_adjust_scores(self):
        self.manager.adjuster.set_bias("quality", -0.1, 0.8)
        adjusted = self.manager.adjust_scores({"quality": 0.7})
        assert "quality" in adjusted
        assert adjusted["quality"] != 0.7

    def test_evaluate_threshold(self):
        result = self.manager.evaluate_threshold("quality", 0.8)
        assert result["status"] in ("pass", "excellent")

    def test_health(self):
        self.manager.run_calibration_cycle({"a": 0.5}, {"a": 0.7})
        health = self.manager.get_health()
        assert health["total_cycles"] == 1
        assert health["profiles"] >= 1

    def test_cycle_count(self):
        self.manager.run_calibration_cycle({"a": 0.5}, {"a": 0.7})
        self.manager.run_calibration_cycle({"a": 0.6}, {"a": 0.8})
        assert self.manager.cycle_count == 2

    def test_events(self):
        self.manager.run_calibration_cycle({"a": 0.5}, {"a": 0.7})
        assert len(self.manager.events) == 1

    def test_get_recent_cycles(self):
        for _ in range(3):
            self.manager.run_calibration_cycle({"a": 0.5}, {"a": 0.7})
        assert len(self.manager.get_recent_cycles(2)) == 2

    def test_manager_components(self):
        assert self.manager.thresholds is not None
        assert self.manager.adjuster is not None
        assert self.manager.confidence_calibrator is not None
        assert self.manager.evaluator is not None
        assert self.manager.benchmark_manager is not None
        assert self.manager.history is not None
        assert self.manager.metrics is not None
        assert self.manager.validator is not None


# ─── Exceptions Tests ─────────────────────────────────────────────────
class TestExceptions:
    def test_base(self):
        assert issubclass(CalibrationError, Exception)

    def test_threshold(self):
        assert issubclass(ThresholdError, CalibrationError)

    def test_benchmark(self):
        assert issubclass(BenchmarkError, CalibrationError)

    def test_validation(self):
        assert issubclass(ValidationError, CalibrationError)


# ─── Integration Tests ────────────────────────────────────────────────
class TestQualityCalibrationIntegration:
    def test_full_calibration_pipeline(self):
        """Test: Evaluate → Calibrate → Adjust → Validate → Benchmark."""
        manager = CalibrationManager()
        predicted = {"engagement": 0.5, "quality": 0.7, "seo": 0.6}
        actual = {"engagement": 0.7, "quality": 0.65, "seo": 0.8}
        result = manager.run_calibration_cycle(predicted, actual)
        assert result.metrics_calibrated == 3
        assert result.is_valid

    def test_threshold_blocks_low_quality(self):
        """Test: Threshold manager catches low quality."""
        manager = CalibrationManager()
        result = manager.evaluate_threshold("quality", 0.1)
        assert result["status"] == "fail"

    def test_adjuster_corrects_bias(self):
        """Test: Adjuster corrects known bias."""
        adjuster = ScoreAdjuster()
        adjuster.set_bias("quality", -0.15, 0.9)
        result = adjuster.adjust("quality", 0.7)
        assert result.adjusted_score < 0.7

    def test_confidence_calibration_accuracy(self):
        """Test: Confidence calibration bins are well-formed."""
        calibrator = ConfidenceCalibrator()
        predictions = [
            {"confidence": c, "correct": c > 0.5}
            for c in [0.1, 0.3, 0.5, 0.7, 0.9, 0.2, 0.8, 0.4, 0.6, 0.95]
        ]
        bins = calibrator.calibrate(predictions)
        assert len(bins) >= 1
        ece = calibrator.get_overall_ece()
        assert ece >= 0

    def test_benchmark_tracking(self):
        """Test: Benchmarks track improvement over time."""
        manager = BenchmarkManager()
        manager.create_run("quality", {"engagement": 0.5})
        manager.create_run("quality", {"engagement": 0.8})
        improvement = manager.get_improvement("quality")
        assert improvement > 0

    def test_history_tracks_changes(self):
        """Test: Calibration history records bias changes."""
        history = CalibrationHistory()
        history.record("quality", 0.1, 0.05, trigger="manual")
        entries = history.get_metric_history("quality")
        assert len(entries) == 1
        assert entries[0].bias_change == -0.05
