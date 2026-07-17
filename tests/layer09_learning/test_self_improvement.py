"""Tests for Layer 9 Module 6 — Self-Improvement Loop."""
from layers.layer09_learning.modules.self_improvement.improvement_cycle import (
    ImprovementCycle,
)
from layers.layer09_learning.modules.self_improvement.mistake_detector import (
    MistakeDetector, DetectedMistake,
)
from layers.layer09_learning.modules.self_improvement.weakness_analyzer import (
    WeaknessAnalyzer, Weakness,
)
from layers.layer09_learning.modules.self_improvement.improvement_actions import (
    ImprovementActionManager, ImprovementAction,
)
from layers.layer09_learning.modules.self_improvement.experiment_runner import (
    ExperimentRunner, Experiment,
)
from layers.layer09_learning.modules.self_improvement.improvement_tracker import ImprovementTracker
from layers.layer09_learning.modules.self_improvement.rollback_manager import RollbackManager
from layers.layer09_learning.modules.self_improvement.improvement_metrics import ImprovementMetrics
from layers.layer09_learning.modules.self_improvement.improvement_history import ImprovementHistory
from layers.layer09_learning.modules.self_improvement.self_improvement_manager import (
    SelfImprovementManager, ImprovementCycleResult,
)
from layers.layer09_learning.modules.self_improvement.exceptions import (
    SelfImprovementError, DetectionError, ExperimentError, RollbackError,
)


# ─── ImprovementCycle Tests ──────────────────────────────────────────
class TestImprovementCycle:
    def test_create(self):
        c = ImprovementCycle("optimization", "Test cycle")
        assert c.cycle_id.startswith("icy_")
        assert c.status == "planned"
        assert c.title == "Test cycle"

    def test_start(self):
        c = ImprovementCycle()
        c.start()
        assert c.status == "running"
        assert c.is_active is True

    def test_complete(self):
        c = ImprovementCycle()
        c.start()
        c.complete(3)
        assert c.status == "completed"
        assert c.improvements_made == 3
        assert c.duration_ms >= 0

    def test_fail(self):
        c = ImprovementCycle()
        c.start()
        c.fail("API error")
        assert c.status == "failed"
        assert c.metadata.get("failure_reason") == "API error"

    def test_rollback(self):
        c = ImprovementCycle()
        c.start()
        c.complete(1)
        c.rollback_available = True
        c.rollback()
        assert c.status == "rolled_back"

    def test_rollback_not_available(self):
        c = ImprovementCycle()
        c.start()
        c.complete(1)
        c.rollback()
        assert c.status == "completed"

    def test_success(self):
        c = ImprovementCycle()
        c.start()
        c.complete(2)
        assert c.success is True

    def test_success_zero_improvements(self):
        c = ImprovementCycle()
        c.start()
        c.complete(0)
        assert c.success is False

    def test_invalid_type(self):
        c = ImprovementCycle("invalid")
        assert c.cycle_type == "optimization"

    def test_to_dict(self):
        c = ImprovementCycle("experiment", "Test")
        d = c.to_dict()
        assert "cycle_id" in d
        assert d["cycle_type"] == "experiment"


# ─── DetectedMistake Tests ────────────────────────────────────────────
class TestDetectedMistake:
    def test_create(self):
        m = DetectedMistake("content", "high")
        assert m.mistake_id.startswith("mdt_")
        assert m.category == "content"
        assert m.severity == "high"

    def test_invalid_category(self):
        m = DetectedMistake("invalid", "medium")
        assert m.category == "content"

    def test_to_dict(self):
        m = DetectedMistake("seo", "critical")
        m.description = "Low SEO"
        d = m.to_dict()
        assert d["category"] == "seo"
        assert d["severity"] == "critical"


# ─── MistakeDetector Tests ────────────────────────────────────────────
class TestMistakeDetector:
    def setup_method(self):
        self.detector = MistakeDetector()

    def test_detect_from_metrics(self):
        metrics = {"engagement": 0.1, "reach": 0.8, "quality": 0.2}
        thresholds = {"engagement": 0.5, "quality": 0.5}
        mistakes = self.detector.detect_from_metrics(metrics, thresholds)
        assert len(mistakes) == 2

    def test_detect_from_metrics_no_issues(self):
        metrics = {"engagement": 0.8, "reach": 0.9}
        thresholds = {"engagement": 0.5}
        mistakes = self.detector.detect_from_metrics(metrics, thresholds)
        assert len(mistakes) == 0

    def test_detect_from_quality(self):
        scores = {"grammar": 0.9, "seo": 0.2, "readability": 0.4}
        mistakes = self.detector.detect_from_quality(scores, min_score=0.5)
        assert len(mistakes) == 2

    def test_detect_from_quality_critical(self):
        scores = {"safety": 0.1}
        mistakes = self.detector.detect_from_quality(scores)
        assert mistakes[0].severity == "critical"

    def test_detect_from_feedback(self):
        feedback = [
            {"negative": True, "description": "Too formal", "category": "tone", "severity": "low"},
            {"negative": False, "description": "Good post"},
        ]
        mistakes = self.detector.detect_from_feedback(feedback)
        assert len(mistakes) == 1

    def test_get_mistakes_by_category(self):
        self.detector.detect_from_quality({"grammar": 0.2, "seo": 0.3})
        content = self.detector.get_mistakes(category="content")
        assert len(content) == 2

    def test_get_critical(self):
        self.detector.detect_from_quality({"safety": 0.1})
        critical = self.detector.get_critical()
        assert len(critical) == 1

    def test_mistake_count(self):
        self.detector.detect_from_quality({"a": 0.2, "b": 0.3})
        assert self.detector.mistake_count == 2

    def test_detection_count(self):
        self.detector.detect_from_metrics({}, {})
        self.detector.detect_from_metrics({}, {})
        assert self.detector.detection_count == 2


# ─── Weakness Tests ───────────────────────────────────────────────────
class TestWeakness:
    def test_create(self):
        w = Weakness("engagement")
        assert w.weakness_id.startswith("wka_")
        assert w.area == "engagement"

    def test_to_dict(self):
        w = Weakness("seo")
        w.severity = "high"
        d = w.to_dict()
        assert d["area"] == "seo"
        assert d["severity"] == "high"


# ─── WeaknessAnalyzer Tests ──────────────────────────────────────────
class TestWeaknessAnalyzer:
    def setup_method(self):
        self.analyzer = WeaknessAnalyzer()

    def test_analyze_basic(self):
        issues = [
            {"area": "engagement", "severity": "high", "impact": 0.7},
            {"area": "engagement", "severity": "medium", "impact": 0.5},
            {"area": "seo", "severity": "low", "impact": 0.3},
        ]
        weaknesses = self.analyzer.analyze(issues)
        assert len(weaknesses) >= 1

    def test_analyze_no_recurring(self):
        issues = [{"area": "unique", "severity": "medium", "impact": 0.5}]
        weaknesses = self.analyzer.analyze(issues, min_frequency=3)
        assert len(weaknesses) == 0

    def test_analyze_severity_propagation(self):
        issues = [
            {"area": "safety", "severity": "critical", "impact": 0.9},
            {"area": "safety", "severity": "low", "impact": 0.3},
        ]
        weaknesses = self.analyzer.analyze(issues)
        assert weaknesses[0].severity == "critical"

    def test_get_by_severity(self):
        issues = [
            {"area": "a", "severity": "high", "impact": 0.8},
            {"area": "a", "severity": "high", "impact": 0.7},
            {"area": "b", "severity": "low", "impact": 0.2},
            {"area": "b", "severity": "low", "impact": 0.1},
        ]
        self.analyzer.analyze(issues)
        high = self.analyzer.get_by_severity("high")
        assert len(high) == 1

    def test_analysis_count(self):
        self.analyzer.analyze([])
        self.analyzer.analyze([])
        assert self.analyzer.analysis_count == 2

    def test_weakness_count(self):
        issues = [{"area": "x", "severity": "medium", "impact": 0.5}] * 3
        self.analyzer.analyze(issues)
        assert self.analyzer.weakness_count == 1


# ─── ImprovementAction Tests ──────────────────────────────────────────
class TestImprovementAction:
    def test_create(self):
        a = ImprovementAction("fix", "high")
        assert a.action_id.startswith("ima_")
        assert a.action_type == "fix"
        assert a.priority == "high"
        assert a.status == "planned"

    def test_complete(self):
        a = ImprovementAction()
        a.complete(0.8)
        assert a.status == "completed"
        assert a.actual_impact == 0.8
        assert a.is_completed is True

    def test_impact_delta(self):
        a = ImprovementAction()
        a.expected_impact = 0.5
        a.actual_impact = 0.8
        assert a.impact_delta == 0.3

    def test_invalid_type(self):
        a = ImprovementAction("invalid")
        assert a.action_type == "fix"

    def test_to_dict(self):
        a = ImprovementAction("optimize", "critical")
        a.title = "Fix SEO"
        d = a.to_dict()
        assert d["action_type"] == "optimize"
        assert d["priority"] == "critical"


# ─── ImprovementActionManager Tests ───────────────────────────────────
class TestImprovementActionManager:
    def setup_method(self):
        self.manager = ImprovementActionManager()

    def test_create(self):
        action = self.manager.create("fix", "high", "Fix grammar", "content")
        assert action.title == "Fix grammar"
        assert self.manager.action_count == 1

    def test_create_from_mistakes(self):
        mistakes = [
            {"description": "Low SEO", "category": "seo", "severity": "high", "mistake_id": "m1"},
            {"description": "Bad grammar", "category": "content", "severity": "medium", "mistake_id": "m2"},
        ]
        actions = self.manager.create_from_mistakes(mistakes)
        assert len(actions) == 2

    def test_complete_action(self):
        action = self.manager.create("fix", "medium", "Test")
        assert self.manager.complete_action(action.action_id, 0.7) is True
        assert action.status == "completed"

    def test_complete_nonexistent(self):
        assert self.manager.complete_action("fake") is False

    def test_get_by_status(self):
        self.manager.create("fix", "medium", "A")
        self.manager.create("fix", "high", "B")
        planned = self.manager.get_actions(status="planned")
        assert len(planned) == 2

    def test_get_completed(self):
        a = self.manager.create("fix", "medium", "A")
        a.complete(0.5)
        assert len(self.manager.get_completed()) == 1


# ─── Experiment Tests ─────────────────────────────────────────────────
class TestExperiment:
    def test_create(self):
        e = Experiment("New tone improves engagement")
        assert e.experiment_id.startswith("exp_")
        assert e.status == "hypothesis"

    def test_start(self):
        e = Experiment("Test")
        e.start()
        assert e.status == "running"

    def test_conclude(self):
        e = Experiment("Test")
        e.start()
        e.control_value = 0.5
        e.treatment_value = 0.7
        e.conclude("treatment", 0.98)
        assert e.status == "concluded"
        assert e.confidence == 0.98

    def test_improvement_pct(self):
        e = Experiment("Test")
        e.control_value = 100
        e.treatment_value = 150
        assert e.improvement_pct == 50.0

    def test_improvement_pct_zero_control(self):
        e = Experiment("Test")
        e.control_value = 0
        e.treatment_value = 50
        assert e.improvement_pct == 0.0

    def test_is_significant(self):
        e = Experiment("Test")
        e.confidence = 0.98
        e.sample_size = 50
        assert e.is_significant is True

    def test_not_significant(self):
        e = Experiment("Test")
        e.confidence = 0.8
        e.sample_size = 10
        assert e.is_significant is False

    def test_to_dict(self):
        e = Experiment("Test hypothesis")
        d = e.to_dict()
        assert "experiment_id" in d
        assert d["hypothesis"] == "Test hypothesis"


# ─── ExperimentRunner Tests ───────────────────────────────────────────
class TestExperimentRunner:
    def setup_method(self):
        self.runner = ExperimentRunner()

    def test_create_experiment(self):
        exp = self.runner.create_experiment("Hypothesis", "engagement", 0.5)
        assert exp.hypothesis == "Hypothesis"
        assert self.runner.experiment_count == 1

    def test_record_treatment(self):
        exp = self.runner.create_experiment("Test", "engagement", 0.5)
        result = self.runner.record_treatment(exp.experiment_id, "engagement", 0.8, 30)
        assert result is not None
        assert result.treatment_value == 0.8

    def test_record_treatment_nonexistent(self):
        assert self.runner.record_treatment("fake", "m", 0.5) is None

    def test_evaluate(self):
        exp = self.runner.create_experiment("Test", "engagement", 0.5)
        exp.treatment_value = 0.7
        result = self.runner.evaluate(exp.experiment_id, 0.95)
        assert result is not None
        assert result.conclusion == "treatment"

    def test_evaluate_control_wins(self):
        exp = self.runner.create_experiment("Test", "engagement", 0.8)
        exp.treatment_value = 0.5
        self.runner.evaluate(exp.experiment_id, 0.95)
        assert exp.conclusion == "control"

    def test_get_significant(self):
        exp = self.runner.create_experiment("Test")
        exp.confidence = 0.98
        exp.sample_size = 50
        sig = self.runner.get_significant()
        assert len(sig) == 1

    def test_get_experiments_filtered(self):
        self.runner.create_experiment("A")
        self.runner.create_experiment("B")
        assert len(self.runner.get_experiments("hypothesis")) == 2


# ─── ImprovementTracker Tests ─────────────────────────────────────────
class TestImprovementTracker:
    def setup_method(self):
        self.tracker = ImprovementTracker()

    def test_take_snapshot(self):
        snap = self.tracker.take_snapshot(0.8, weaknesses_resolved=2, actions_completed=3)
        assert snap.score == 0.8
        assert self.tracker.snapshot_count == 1

    def test_get_improvement_rate(self):
        self.tracker.take_snapshot(0.5)
        self.tracker.take_snapshot(0.8)
        rate = self.tracker.get_improvement_rate()
        assert rate > 0

    def test_get_improvement_rate_insufficient(self):
        assert self.tracker.get_improvement_rate() == 0.0

    def test_get_trend_improving(self):
        self.tracker.take_snapshot(0.5)
        self.tracker.take_snapshot(0.6)
        self.tracker.take_snapshot(0.7)
        assert self.tracker.get_trend() == "improving"

    def test_get_trend_declining(self):
        self.tracker.take_snapshot(0.8)
        self.tracker.take_snapshot(0.7)
        self.tracker.take_snapshot(0.6)
        assert self.tracker.get_trend() == "declining"

    def test_get_trend_stable(self):
        self.tracker.take_snapshot(0.5)
        self.tracker.take_snapshot(0.5)
        assert self.tracker.get_trend() == "stable"

    def test_get_best_score(self):
        self.tracker.take_snapshot(0.3)
        self.tracker.take_snapshot(0.9)
        self.tracker.take_snapshot(0.6)
        assert self.tracker.get_best_score() == 0.9

    def test_get_latest(self):
        self.tracker.take_snapshot(0.5)
        self.tracker.take_snapshot(0.8)
        latest = self.tracker.get_latest()
        assert latest.score == 0.8

    def test_get_latest_empty(self):
        assert self.tracker.get_latest() is None


# ─── RollbackManager Tests ────────────────────────────────────────────
class TestRollbackManager:
    def setup_method(self):
        self.manager = RollbackManager()

    def test_save_point(self):
        point = self.manager.save_point("before experiment", {"score": 0.5})
        assert point.point_id.startswith("rbp_")
        assert self.manager.point_count == 1

    def test_rollback(self):
        point = self.manager.save_point("test", {"score": 0.5})
        data = self.manager.rollback(point.point_id)
        assert data is not None
        assert data["score"] == 0.5
        assert self.manager.rollback_count == 1

    def test_rollback_already_used(self):
        point = self.manager.save_point("test", {"score": 0.5})
        self.manager.rollback(point.point_id)
        result = self.manager.rollback(point.point_id)
        assert result is None

    def test_rollback_nonexistent(self):
        assert self.manager.rollback("fake") is None

    def test_get_points(self):
        self.manager.save_point("a", {})
        self.manager.save_point("b", {})
        assert len(self.manager.get_points()) == 2

    def test_get_points_restorable(self):
        p1 = self.manager.save_point("a", {})
        self.manager.save_point("b", {})
        self.manager.rollback(p1.point_id)
        restorable = self.manager.get_points(restorable_only=True)
        assert len(restorable) == 1

    def test_get_latest(self):
        self.manager.save_point("a", {})
        p2 = self.manager.save_point("b", {})
        assert self.manager.get_latest().point_id == p2.point_id

    def test_point_to_dict(self):
        point = self.manager.save_point("test", {})
        d = point.to_dict()
        assert "point_id" in d
        assert d["label"] == "test"


# ─── ImprovementMetrics Tests ─────────────────────────────────────────
class TestImprovementMetrics:
    def setup_method(self):
        self.metrics = ImprovementMetrics()

    def test_record_cycle(self):
        self.metrics.record_cycle(0.8, True)
        assert self.metrics.get_cycle_success_rate() == 1.0

    def test_record_mistakes(self):
        self.metrics.record_mistakes(5)
        assert self.metrics.get_summary()["total_mistakes_detected"] == 5

    def test_record_weaknesses(self):
        self.metrics.record_weaknesses(3)
        assert self.metrics.get_summary()["total_weaknesses_found"] == 3

    def test_record_action(self):
        self.metrics.record_action(completed=True)
        self.metrics.record_action(completed=False)
        assert self.metrics.get_action_completion_rate() == 0.5

    def test_record_experiment(self):
        self.metrics.record_experiment()
        assert self.metrics.get_summary()["total_experiments"] == 1

    def test_record_rollback(self):
        self.metrics.record_rollback()
        assert self.metrics.get_summary()["total_rollbacks"] == 1

    def test_summary(self):
        self.metrics.record_cycle(0.7, True)
        self.metrics.record_mistakes(2)
        summary = self.metrics.get_summary()
        assert "total_cycles" in summary

    def test_reset(self):
        self.metrics.record_cycle(0.8, True)
        self.metrics.reset()
        assert self.metrics.get_cycle_success_rate() == 0.0

    def test_no_data(self):
        assert self.metrics.get_cycle_success_rate() == 0.0
        assert self.metrics.get_action_completion_rate() == 0.0
        assert self.metrics.get_avg_score() == 0.0


# ─── ImprovementHistory Tests ─────────────────────────────────────────
class TestImprovementHistory:
    def setup_method(self):
        self.history = ImprovementHistory()

    def test_record(self):
        entry = self.history.record("improvement", "Fixed SEO", score_before=0.5, score_after=0.8)
        assert entry.title == "Fixed SEO"
        assert entry.improvement_delta == 0.3

    def test_get_entries(self):
        self.history.record("improvement", "A")
        self.history.record("regression", "B")
        assert len(self.history.get_entries()) == 2

    def test_get_improvements(self):
        self.history.record("improvement", "A", score_before=0.5, score_after=0.8)
        self.history.record("regression", "B", score_before=0.8, score_after=0.5)
        assert len(self.history.get_improvements()) == 1

    def test_get_regressions(self):
        self.history.record("improvement", "A", score_before=0.5, score_after=0.8)
        self.history.record("regression", "B", score_before=0.8, score_after=0.5)
        assert len(self.history.get_regressions()) == 1

    def test_milestones(self):
        self.history.record("improvement", "A", score_after=0.9)
        milestones = self.history.get_milestones()
        assert len(milestones) >= 1
        assert any(m["threshold"] == 0.9 for m in milestones)

    def test_entry_to_dict(self):
        entry = self.history.record("improvement", "Test", score_before=0.5, score_after=0.8)
        d = entry.to_dict()
        assert "improvement_delta" in d
        assert d["improvement_delta"] == 0.3

    def test_entry_count(self):
        self.history.record("improvement", "A")
        assert self.history.entry_count == 1


# ─── ImprovementCycleResult Tests ─────────────────────────────────────
class TestImprovementCycleResult:
    def test_create(self):
        r = ImprovementCycleResult()
        assert r.cycle_id.startswith("siy_")

    def test_to_dict(self):
        r = ImprovementCycleResult()
        r.mistakes_found = 3
        d = r.to_dict()
        assert d["mistakes_found"] == 3


# ─── SelfImprovementManager Tests ─────────────────────────────────────
class TestSelfImprovementManager:
    def setup_method(self):
        self.manager = SelfImprovementManager()

    def test_run_cycle_minimal(self):
        result = self.manager.run_improvement_cycle(current_score=0.7)
        assert result.cycle_id.startswith("siy_")
        assert result.current_score == 0.7

    def test_run_cycle_with_quality(self):
        quality = {"grammar": 0.9, "seo": 0.2}
        result = self.manager.run_improvement_cycle(quality_scores=quality, current_score=0.6)
        assert result.mistakes_found >= 1

    def test_run_cycle_with_feedback(self):
        feedback = [{"negative": True, "description": "Too long", "category": "content", "severity": "medium"}]
        result = self.manager.run_improvement_cycle(feedback=feedback, current_score=0.5)
        assert result.mistakes_found >= 1

    def test_run_cycle_with_issues(self):
        issues = [
            {"area": "engagement", "severity": "high", "impact": 0.7},
            {"area": "engagement", "severity": "medium", "impact": 0.5},
        ]
        result = self.manager.run_improvement_cycle(issues=issues, current_score=0.6)
        assert result.weaknesses_found >= 1

    def test_create_experiment(self):
        exp = self.manager.create_experiment("Test hypothesis", "engagement", 0.5)
        assert exp.hypothesis == "Test hypothesis"

    def test_save_checkpoint(self):
        result = self.manager.save_checkpoint("before test", {"score": 0.5})
        assert result["label"] == "before test"

    def test_rollback_to(self):
        point = self.manager.save_checkpoint("test", {"score": 0.5})
        data = self.manager.rollback_to(point["point_id"])
        assert data is not None

    def test_health(self):
        self.manager.run_improvement_cycle(current_score=0.7)
        health = self.manager.get_health()
        assert health["total_cycles"] == 1
        assert "metrics" in health

    def test_cycle_count(self):
        self.manager.run_improvement_cycle(current_score=0.5)
        self.manager.run_improvement_cycle(current_score=0.7)
        assert self.manager.cycle_count == 2

    def test_events(self):
        self.manager.run_improvement_cycle(current_score=0.6)
        assert len(self.manager.events) == 1

    def test_get_recent_cycles(self):
        for _ in range(3):
            self.manager.run_improvement_cycle(current_score=0.5)
        assert len(self.manager.get_recent_cycles(2)) == 2

    def test_manager_components(self):
        assert self.manager.mistake_detector is not None
        assert self.manager.weakness_analyzer is not None
        assert self.manager.action_manager is not None
        assert self.manager.experiment_runner is not None
        assert self.manager.tracker is not None
        assert self.manager.rollback_manager is not None
        assert self.manager.metrics is not None
        assert self.manager.history is not None


# ─── Exceptions Tests ─────────────────────────────────────────────────
class TestExceptions:
    def test_base(self):
        assert issubclass(SelfImprovementError, Exception)

    def test_detection(self):
        assert issubclass(DetectionError, SelfImprovementError)

    def test_experiment(self):
        assert issubclass(ExperimentError, SelfImprovementError)

    def test_rollback(self):
        assert issubclass(RollbackError, SelfImprovementError)


# ─── Integration Tests ────────────────────────────────────────────────
class TestSelfImprovementIntegration:
    def test_full_improvement_pipeline(self):
        """Test: Detect → Analyze → Actions → Track → History."""
        manager = SelfImprovementManager()
        quality = {"grammar": 0.9, "seo": 0.2, "readability": 0.4}
        feedback = [{"negative": True, "description": "Too formal", "category": "tone", "severity": "low"}]
        issues = [
            {"area": "engagement", "severity": "high", "impact": 0.7},
            {"area": "engagement", "severity": "medium", "impact": 0.5},
        ]
        result = manager.run_improvement_cycle(
            quality_scores=quality, feedback=feedback, issues=issues, current_score=0.6,
        )
        assert result.mistakes_found >= 2
        assert result.actions_created >= 2

    def test_experiment_lifecycle(self):
        """Test: Create → Record → Evaluate experiment."""
        manager = SelfImprovementManager()
        exp = manager.create_experiment("New tone improves engagement", "engagement", 0.5)
        exp.start()
        exp.treatment_value = 0.7
        exp.sample_size = 50
        manager.experiment_runner.evaluate(exp.experiment_id, 0.98)
        assert exp.conclusion == "treatment"
        assert exp.is_significant

    def test_rollback_flow(self):
        """Test: Save checkpoint → Modify → Rollback."""
        manager = SelfImprovementManager()
        point = manager.save_checkpoint("before experiment", {"score": 0.5, "config": "v1"})
        data = manager.rollback_to(point["point_id"])
        assert data["score"] == 0.5

    def test_tracking_over_time(self):
        """Test: Multiple snapshots show improvement trend."""
        tracker = ImprovementTracker()
        for score in [0.4, 0.5, 0.6, 0.7, 0.8]:
            tracker.take_snapshot(score)
        assert tracker.get_trend() == "improving"
        assert tracker.get_improvement_rate() > 0

    def test_weakness_drives_actions(self):
        """Test: Detected weaknesses create improvement actions."""
        analyzer = WeaknessAnalyzer()
        action_mgr = ImprovementActionManager()
        issues = [
            {"area": "seo", "severity": "high", "impact": 0.8},
            {"area": "seo", "severity": "medium", "impact": 0.6},
        ]
        weaknesses = analyzer.analyze(issues)
        assert len(weaknesses) >= 1
        mistakes = [{"description": w.description, "category": w.area, "severity": w.severity}
                    for w in weaknesses]
        actions = action_mgr.create_from_mistakes(mistakes)
        assert len(actions) >= 1
