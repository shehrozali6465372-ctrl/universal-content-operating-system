"""Tests for Layer 9 Module 1 — Learning Engine."""
from layers.layer09_learning.modules.learning_engine.learning_signal import (
    LearningSignal, SIGNAL_SOURCES, SIGNAL_TYPES,
)
from layers.layer09_learning.modules.learning_engine.feedback_collector import (
    FeedbackCollector, FeedbackSource,
)
from layers.layer09_learning.modules.learning_engine.performance_comparator import (
    PerformanceComparator, ComparisonResult,
)
from layers.layer09_learning.modules.learning_engine.pattern_detector import (
    PatternDetector, DetectedPattern,
)
from layers.layer09_learning.modules.learning_engine.lesson_generator import (
    LessonGenerator, Lesson,
)
from layers.layer09_learning.modules.learning_engine.improvement_planner import (
    ImprovementPlanner, Improvement, PRIORITY_LEVELS,
)
from layers.layer09_learning.modules.learning_engine.learning_memory import (
    LearningMemory, MemoryEntry,
)
from layers.layer09_learning.modules.learning_engine.confidence_tracker import (
    ConfidenceTracker, ConfidenceRecord,
)
from layers.layer09_learning.modules.learning_engine.learning_metrics import LearningMetrics
from layers.layer09_learning.modules.learning_engine.exceptions import (
    LearningError, SignalCollectionError, LessonGenerationError, MemoryStorageError,
)
from layers.layer09_learning.modules.learning_engine.learning_manager import (
    LearningManager, LearningResult,
)


# ─── LearningSignal Tests ─────────────────────────────────────────────
class TestLearningSignal:
    def setup_method(self):
        self.signal = LearningSignal(
            source="analytics",
            signal_type="engagement",
            metric_name="likes",
            value=150.0,
        )

    def test_create_default(self):
        s = LearningSignal()
        assert s.source == "analytics"
        assert s.signal_type == "engagement"
        assert s.metric_name == ""
        assert s.value == 0.0
        assert s.confidence == 0.8
        assert s.platform == ""
        assert s.content_id == ""
        assert s.signal_id.startswith("sig_")

    def test_create_with_args(self):
        s = self.signal
        assert s.source == "analytics"
        assert s.signal_type == "engagement"
        assert s.metric_name == "likes"
        assert s.value == 150.0

    def test_invalid_source_falls_back(self):
        s = LearningSignal(source="invalid_source")
        assert s.source == "system"

    def test_invalid_type_falls_back(self):
        s = LearningSignal(signal_type="invalid_type")
        assert s.signal_type == "engagement"

    def test_change_positive(self):
        self.signal.previous_value = 100.0
        assert self.signal.change == 50.0

    def test_change_negative(self):
        self.signal.previous_value = 200.0
        assert self.signal.change == -50.0

    def test_change_none_when_no_previous(self):
        assert self.signal.change is None

    def test_change_pct_positive(self):
        self.signal.previous_value = 100.0
        assert self.signal.change_pct == 50.0

    def test_change_pct_zero_previous(self):
        self.signal.previous_value = 0.0
        assert self.signal.change_pct is None

    def test_change_pct_none_when_no_previous(self):
        assert self.signal.change_pct is None

    def test_is_positive_with_change(self):
        self.signal.previous_value = 100.0
        assert self.signal.is_positive() is True

    def test_is_negative_with_change(self):
        self.signal.previous_value = 200.0
        assert self.signal.is_positive() is False

    def test_is_positive_no_change_positive_value(self):
        assert self.signal.is_positive() is True

    def test_is_positive_no_change_zero_value(self):
        s = LearningSignal(value=0.0)
        assert s.is_positive() is False

    def test_to_dict(self):
        d = self.signal.to_dict()
        assert "signal_id" in d
        assert d["source"] == "analytics"
        assert d["signal_type"] == "engagement"
        assert d["metric_name"] == "likes"
        assert d["value"] == 150.0
        assert d["confidence"] == 0.8

    def test_to_dict_with_previous(self):
        self.signal.previous_value = 100.0
        d = self.signal.to_dict()
        assert d["previous_value"] == 100.0
        assert d["change"] == 50.0

    def test_signal_sources_valid(self):
        assert "analytics" in SIGNAL_SOURCES
        assert "human" in SIGNAL_SOURCES
        assert "platform" in SIGNAL_SOURCES

    def test_signal_types_valid(self):
        assert "engagement" in SIGNAL_TYPES
        assert "conversion" in SIGNAL_TYPES
        assert "failure" in SIGNAL_TYPES


# ─── FeedbackSource Tests ─────────────────────────────────────────────
class TestFeedbackSource:
    def test_create_default(self):
        fs = FeedbackSource()
        assert fs.source_id == ""
        assert fs.name == ""
        assert fs.enabled is True
        assert fs.fetcher is None

    def test_create_with_args(self):
        fs = FeedbackSource(source_id="s1", name="Analytics", source_type="analytics")
        assert fs.source_id == "s1"
        assert fs.name == "Analytics"
        assert fs.source_type == "analytics"

    def test_to_dict(self):
        fs = FeedbackSource(source_id="s1", name="Test", source_type="human")
        d = fs.to_dict()
        assert d["source_id"] == "s1"
        assert d["name"] == "Test"
        assert d["source_type"] == "human"
        assert d["enabled"] is True


# ─── FeedbackCollector Tests ──────────────────────────────────────────
class TestFeedbackCollector:
    def setup_method(self):
        self.collector = FeedbackCollector()

    def test_create(self):
        assert self.collector.signal_count == 0
        assert self.collector.collection_count == 0

    def test_register_source(self):
        fs = FeedbackSource(source_id="s1", name="Test")
        self.collector.register_source(fs)
        assert len(self.collector.get_sources()) == 1

    def test_unregister_source(self):
        fs = FeedbackSource(source_id="s1")
        self.collector.register_source(fs)
        assert self.collector.unregister_source("s1") is True
        assert len(self.collector.get_sources()) == 0

    def test_unregister_nonexistent(self):
        assert self.collector.unregister_source("missing") is False

    def test_collect_from_source_with_fetcher(self):
        fs = FeedbackSource(source_id="s1", name="Test", source_type="analytics")
        fs.fetcher = lambda: [
            {"type": "engagement", "metric": "likes", "value": 10.0, "platform": "facebook"},
            {"type": "reach", "metric": "impressions", "value": 500.0, "platform": "facebook"},
        ]
        self.collector.register_source(fs)
        signals = self.collector.collect_from_source("s1")
        assert len(signals) == 2
        assert signals[0].metric_name == "likes"
        assert signals[1].metric_name == "impressions"

    def test_collect_from_disabled_source(self):
        fs = FeedbackSource(source_id="s1")
        fs.enabled = False
        fs.fetcher = lambda: [{"type": "engagement", "metric": "likes", "value": 10.0}]
        self.collector.register_source(fs)
        signals = self.collector.collect_from_source("s1")
        assert len(signals) == 0

    def test_collect_from_source_no_fetcher(self):
        fs = FeedbackSource(source_id="s1")
        self.collector.register_source(fs)
        signals = self.collector.collect_from_source("s1")
        assert len(signals) == 0

    def test_collect_from_source_exception(self):
        fs = FeedbackSource(source_id="s1")
        fs.fetcher = lambda: (_ for _ in ()).throw(Exception("API error"))
        self.collector.register_source(fs)
        signals = self.collector.collect_from_source("s1")
        assert len(signals) == 0

    def test_collect_all(self):
        fs1 = FeedbackSource(source_id="s1", source_type="analytics")
        fs1.fetcher = lambda: [{"type": "engagement", "metric": "a", "value": 1.0}]
        fs2 = FeedbackSource(source_id="s2", source_type="human")
        fs2.fetcher = lambda: [{"type": "engagement", "metric": "b", "value": 2.0}]
        self.collector.register_source(fs1)
        self.collector.register_source(fs2)
        signals = self.collector.collect_all()
        assert len(signals) == 2

    def test_add_signal(self):
        sig = LearningSignal(source="human", metric_name="feedback", value=5.0)
        self.collector.add_signal(sig)
        assert self.collector.signal_count == 1

    def test_get_signals_filter_by_source(self):
        s1 = LearningSignal(source="analytics", metric_name="a", value=1.0)
        s2 = LearningSignal(source="human", metric_name="b", value=2.0)
        self.collector.add_signal(s1)
        self.collector.add_signal(s2)
        result = self.collector.get_signals(source="analytics")
        assert len(result) == 1
        assert result[0].source == "analytics"

    def test_get_signals_filter_by_type(self):
        s1 = LearningSignal(signal_type="engagement", value=1.0)
        s2 = LearningSignal(signal_type="conversion", value=2.0)
        self.collector.add_signal(s1)
        self.collector.add_signal(s2)
        result = self.collector.get_signals(signal_type="conversion")
        assert len(result) == 1

    def test_get_signals_filter_by_platform(self):
        s1 = LearningSignal(value=1.0)
        s1.platform = "facebook"
        s2 = LearningSignal(value=2.0)
        s2.platform = "linkedin"
        self.collector.add_signal(s1)
        self.collector.add_signal(s2)
        result = self.collector.get_signals(platform="linkedin")
        assert len(result) == 1

    def test_get_signals_limit(self):
        for i in range(10):
            self.collector.add_signal(LearningSignal(value=float(i)))
        result = self.collector.get_signals(limit=3)
        assert len(result) == 3

    def test_collection_count_increments(self):
        fs = FeedbackSource(source_id="s1")
        fs.fetcher = lambda: []
        self.collector.register_source(fs)
        self.collector.collect_from_source("s1")
        assert self.collector.collection_count == 1

    def test_signal_set_from_item(self):
        fs = FeedbackSource(source_id="s1", source_type="platform")
        fs.fetcher = lambda: [{"type": "growth", "metric": "reach", "value": 100.0, "platform": "x", "content_id": "c1"}]
        self.collector.register_source(fs)
        signals = self.collector.collect_from_source("s1")
        assert signals[0].platform == "x"
        assert signals[0].content_id == "c1"


# ─── ComparisonResult Tests ───────────────────────────────────────────
class TestComparisonResult:
    def test_create_default(self):
        cr = ComparisonResult()
        assert cr.metric_name == ""
        assert cr.previous_value == 0.0
        assert cr.current_value == 0.0
        assert cr.direction == "stable"
        assert cr.significance == "low"

    def test_to_dict(self):
        comp = PerformanceComparator()
        cr = comp.compare("likes", 100.0, 150.0)
        d = cr.to_dict()
        assert d["metric_name"] == "likes"
        assert d["change"] == 50.0
        assert d["direction"] == "growth"
        assert "significance" in d


# ─── PerformanceComparator Tests ──────────────────────────────────────
class TestPerformanceComparator:
    def setup_method(self):
        self.comp = PerformanceComparator()

    def test_compare_growth(self):
        result = self.comp.compare("likes", 100.0, 150.0)
        assert result.direction == "growth"
        assert result.change == 50.0
        assert result.change_pct == 50.0

    def test_compare_decline(self):
        result = self.comp.compare("likes", 200.0, 100.0)
        assert result.direction == "decline"
        assert result.change == -100.0

    def test_compare_stable(self):
        result = self.comp.compare("likes", 100.0, 102.0)
        assert result.direction == "stable"

    def test_compare_zero_previous(self):
        result = self.comp.compare("new_metric", 0.0, 50.0)
        assert result.change_pct == 100.0
        assert result.direction == "growth"

    def test_compare_zero_both(self):
        result = self.comp.compare("m", 0.0, 0.0)
        assert result.change_pct == 0.0
        assert result.direction == "stable"

    def test_significance_high(self):
        result = self.comp.compare("m", 100.0, 130.0)
        assert result.significance == "high"

    def test_significance_medium(self):
        result = self.comp.compare("m", 100.0, 115.0)
        assert result.significance == "medium"

    def test_significance_low(self):
        result = self.comp.compare("m", 100.0, 103.0)
        assert result.significance == "low"

    def test_compare_signals(self):
        prev = [
            LearningSignal(metric_name="likes", value=100.0),
            LearningSignal(metric_name="shares", value=50.0),
        ]
        curr = [
            LearningSignal(metric_name="likes", value=120.0),
            LearningSignal(metric_name="shares", value=30.0),
        ]
        results = self.comp.compare_signals(prev, curr)
        assert len(results) >= 2
        metrics = {r.metric_name: r.direction for r in results}
        assert metrics["likes"] == "growth"
        assert metrics["shares"] == "decline"

    def test_compare_signals_new_metric(self):
        prev = [LearningSignal(metric_name="likes", value=100.0)]
        curr = [
            LearningSignal(metric_name="likes", value=100.0),
            LearningSignal(metric_name="new_metric", value=50.0),
        ]
        results = self.comp.compare_signals(prev, curr)
        assert len(results) == 2

    def test_get_growth_metrics(self):
        self.comp.compare("likes", 100.0, 150.0)
        self.comp.compare("shares", 100.0, 80.0)
        growth = self.comp.get_growth_metrics()
        assert len(growth) == 1
        assert growth[0].metric_name == "likes"

    def test_get_decline_metrics(self):
        self.comp.compare("likes", 100.0, 150.0)
        self.comp.compare("shares", 100.0, 80.0)
        decline = self.comp.get_decline_metrics()
        assert len(decline) == 1
        assert decline[0].metric_name == "shares"

    def test_comparison_count(self):
        self.comp.compare("a", 1, 2)
        self.comp.compare("b", 3, 4)
        assert self.comp.comparison_count == 2

    def test_get_comparisons(self):
        self.comp.compare("a", 1, 2)
        comps = self.comp.get_comparisons()
        assert len(comps) == 1


# ─── DetectedPattern Tests ────────────────────────────────────────────
class TestDetectedPattern:
    def test_create_default(self):
        dp = DetectedPattern()
        assert dp.pattern_type == "repeated"
        assert dp.confidence == 0.0
        assert dp.frequency == 0

    def test_create_with_args(self):
        dp = DetectedPattern("success", "Good performance")
        assert dp.pattern_type == "success"
        assert dp.description == "Good performance"

    def test_invalid_type_falls_back(self):
        dp = DetectedPattern("invalid", "test")
        assert dp.pattern_type == "repeated"

    def test_to_dict(self):
        dp = DetectedPattern("success", "Test")
        dp.confidence = 0.9
        dp.frequency = 5
        d = dp.to_dict()
        assert d["pattern_type"] == "success"
        assert d["confidence"] == 0.9
        assert d["frequency"] == 5


# ─── PatternDetector Tests ────────────────────────────────────────────
class TestPatternDetector:
    def setup_method(self):
        self.detector = PatternDetector()

    def test_detect_empty(self):
        patterns = self.detector.detect([])
        assert len(patterns) == 0

    def test_detect_success_patterns(self):
        signals = []
        for i in range(5):
            s = LearningSignal(source="analytics", signal_type="engagement", metric_name="likes", value=float(i + 1))
            s.platform = "facebook"
            signals.append(s)
        patterns = self.detector.detect(signals)
        success = [p for p in patterns if p.pattern_type == "success"]
        assert len(success) >= 1
        assert success[0].platform == "facebook"

    def test_detect_failure_patterns(self):
        signals = []
        for i in range(5):
            s = LearningSignal(source="analytics", signal_type="failure", metric_name="errors", value=0.0)
            s.previous_value = 10.0
            signals.append(s)
        patterns = self.detector.detect(signals)
        failures = [p for p in patterns if p.pattern_type == "failure"]
        assert len(failures) >= 1

    def test_detect_repeated_patterns(self):
        signals = []
        for i in range(5):
            s = LearningSignal(metric_name="conversion", value=50.0)
            signals.append(s)
        patterns = self.detector.detect(signals)
        repeated = [p for p in patterns if p.pattern_type == "repeated"]
        assert len(repeated) >= 1

    def test_detection_count_increments(self):
        signals = [LearningSignal(metric_name="m", value=float(i)) for i in range(5)]
        self.detector.detect(signals)
        self.detector.detect(signals)
        assert self.detector.detection_count == 2

    def test_get_patterns_by_type(self):
        signals = []
        for i in range(5):
            s = LearningSignal(metric_name="m", value=float(i))
            s.platform = "x"
            signals.append(s)
        self.detector.detect(signals)
        success = self.detector.get_patterns("success")
        for p in success:
            assert p.pattern_type == "success"

    def test_get_patterns_all(self):
        signals = []
        for i in range(5):
            s = LearningSignal(metric_name="m", value=float(i))
            signals.append(s)
        self.detector.detect(signals)
        all_p = self.detector.get_patterns()
        assert len(all_p) > 0

    def test_pattern_count(self):
        signals = [LearningSignal(metric_name="x", value=float(i)) for i in range(5)]
        self.detector.detect(signals)
        assert self.detector.pattern_count > 0

    def test_min_frequency_enforced(self):
        signals = [LearningSignal(metric_name="rare", value=1.0)]
        patterns = self.detector.detect(signals)
        for p in patterns:
            if "rare" in p.tags:
                assert False, "Should not detect pattern with frequency < 3"


# ─── Lesson Tests ─────────────────────────────────────────────────────
class TestLesson:
    def test_create_default(self):
        lesson = Lesson()
        assert lesson.lesson_type == "insight"
        assert lesson.confidence == 0.0
        assert lesson.version == 1
        assert lesson.lesson_id.startswith("lesn_")

    def test_create_with_args(self):
        lesson = Lesson("best_practice", "Great work")
        assert lesson.lesson_type == "best_practice"
        assert lesson.title == "Great work"

    def test_invalid_type_falls_back(self):
        lesson = Lesson("invalid_type", "Test")
        assert lesson.lesson_type == "insight"

    def test_to_dict(self):
        lesson = Lesson("mistake", "Bad post")
        lesson.confidence = 0.7
        lesson.action_items = ["Fix this"]
        d = lesson.to_dict()
        assert d["lesson_type"] == "mistake"
        assert d["confidence"] == 0.7
        assert d["action_items"] == ["Fix this"]


# ─── LessonGenerator Tests ────────────────────────────────────────────
class TestLessonGenerator:
    def setup_method(self):
        self.gen = LessonGenerator()

    def _make_pattern(self, ptype, platform="", tags=None):
        p = DetectedPattern(ptype, f"Pattern for {ptype}")
        p.confidence = 0.8
        p.frequency = 5
        p.platform = platform
        p.tags = tags or []
        p.pattern_id = f"pat_test_{ptype}"
        return p

    def test_generate_from_success(self):
        pattern = self._make_pattern("success", "facebook")
        lessons = self.gen.generate([pattern])
        assert len(lessons) == 1
        assert lessons[0].lesson_type == "best_practice"
        assert lessons[0].platform == "facebook"
        assert len(lessons[0].action_items) >= 1

    def test_generate_from_failure(self):
        pattern = self._make_pattern("failure", tags=["errors"])
        lessons = self.gen.generate([pattern])
        assert len(lessons) == 1
        assert lessons[0].lesson_type == "mistake"

    def test_generate_from_repeated(self):
        pattern = self._make_pattern("repeated")
        lessons = self.gen.generate([pattern])
        assert len(lessons) == 1
        assert lessons[0].lesson_type == "insight"

    def test_generate_from_generic(self):
        pattern = self._make_pattern("seasonal")
        lessons = self.gen.generate([pattern])
        assert len(lessons) == 1
        assert lessons[0].lesson_type == "recommendation"

    def test_get_lessons_by_type(self):
        p1 = self._make_pattern("success", "facebook")
        p2 = self._make_pattern("failure")
        self.gen.generate([p1, p2])
        best = self.gen.get_lessons("best_practice")
        assert len(best) == 1

    def test_get_lessons_by_platform(self):
        p1 = self._make_pattern("success", "facebook")
        p2 = self._make_pattern("success", "linkedin")
        self.gen.generate([p1, p2])
        fb = self.gen.get_lessons(platform="facebook")
        assert len(fb) == 1

    def test_generation_count(self):
        self.gen.generate([])
        self.gen.generate([])
        assert self.gen.generation_count == 2

    def test_lesson_count(self):
        p = self._make_pattern("success", "x")
        self.gen.generate([p])
        assert self.gen.lesson_count == 1

    def test_get_all_lessons(self):
        p1 = self._make_pattern("success", "a")
        p2 = self._make_pattern("failure")
        self.gen.generate([p1, p2])
        all_l = self.gen.get_all_lessons()
        assert len(all_l) == 2


# ─── Improvement Tests ────────────────────────────────────────────────
class TestImprovement:
    def test_create_default(self):
        imp = Improvement()
        assert imp.priority == "medium"
        assert imp.status == "suggested"
        assert imp.improvement_id.startswith("imp_")

    def test_create_with_args(self):
        imp = Improvement("Fix issue", "high")
        assert imp.title == "Fix issue"
        assert imp.priority == "high"

    def test_invalid_priority_falls_back(self):
        imp = Improvement("Test", "invalid")
        assert imp.priority == "medium"

    def test_to_dict(self):
        imp = Improvement("Test", "critical")
        d = imp.to_dict()
        assert d["priority"] == "critical"
        assert d["status"] == "suggested"


# ─── ImprovementPlanner Tests ─────────────────────────────────────────
class TestImprovementPlanner:
    def setup_method(self):
        self.planner = ImprovementPlanner()

    def _make_lesson(self, ltype, title="Test Lesson", platform=""):
        lesson = Lesson(ltype, title)
        lesson.description = f"Description for {ltype}"
        lesson.platform = platform
        lesson.confidence = 0.8
        return lesson

    def test_plan_from_best_practice(self):
        lesson = self._make_lesson("best_practice", platform="facebook")
        imps = self.planner.plan_from_lessons([lesson])
        assert len(imps) == 1
        assert imps[0].priority == "high"
        assert imps[0].impact == "high"
        assert imps[0].platform == "facebook"

    def test_plan_from_mistake(self):
        lesson = self._make_lesson("mistake")
        imps = self.planner.plan_from_lessons([lesson])
        assert len(imps) == 1
        assert imps[0].priority == "critical"
        assert imps[0].impact == "high"

    def test_plan_from_warning(self):
        lesson = self._make_lesson("warning")
        imps = self.planner.plan_from_lessons([lesson])
        assert len(imps) == 1
        assert imps[0].priority == "medium"

    def test_plan_from_insight(self):
        lesson = self._make_lesson("insight")
        imps = self.planner.plan_from_lessons([lesson])
        assert len(imps) == 1
        assert imps[0].priority == "low"
        assert imps[0].impact == "low"

    def test_prioritize(self):
        self.planner.plan_from_lessons([self._make_lesson("mistake", "A")])
        self.planner.plan_from_lessons([self._make_lesson("insight", "B")])
        self.planner.plan_from_lessons([self._make_lesson("best_practice", "C")])
        sorted_imps = self.planner.prioritize()
        priorities = [i.priority for i in sorted_imps]
        assert priorities == sorted(priorities, key=lambda p: PRIORITY_LEVELS.index(p) if p in PRIORITY_LEVELS else 99)

    def test_get_improvements_by_priority(self):
        self.planner.plan_from_lessons([self._make_lesson("mistake", "A")])
        self.planner.plan_from_lessons([self._make_lesson("insight", "B")])
        critical = self.planner.get_improvements(priority="critical")
        assert len(critical) == 1

    def test_get_improvements_by_platform(self):
        lesson1 = self._make_lesson("mistake", platform="facebook")
        lesson2 = self._make_lesson("mistake", platform="linkedin")
        self.planner.plan_from_lessons([lesson1, lesson2])
        fb = self.planner.get_improvements(platform="facebook")
        assert len(fb) == 1

    def test_planning_count(self):
        self.planner.plan_from_lessons([])
        self.planner.plan_from_lessons([])
        assert self.planner.planning_count == 2

    def test_improvement_count(self):
        self.planner.plan_from_lessons([self._make_lesson("mistake"), self._make_lesson("insight")])
        assert self.planner.improvement_count == 2

    def test_source_lesson_set(self):
        lesson = self._make_lesson("best_practice")
        imps = self.planner.plan_from_lessons([lesson])
        assert imps[0].source_lesson == lesson.lesson_id


# ─── MemoryEntry Tests ────────────────────────────────────────────────
class TestMemoryEntry:
    def test_create_default(self):
        me = MemoryEntry()
        assert me.entry_id.startswith("mem_")
        assert me.archived is False
        assert me.version == 1
        assert me.lesson is None

    def test_create_with_lesson(self):
        lesson = Lesson("best_practice", "Test")
        me = MemoryEntry(lesson=lesson)
        assert me.lesson is not None
        assert me.improvement is None

    def test_create_with_improvement(self):
        imp = Improvement("Test imp")
        me = MemoryEntry(improvement=imp)
        assert me.improvement is not None
        assert me.lesson is None

    def test_to_dict(self):
        me = MemoryEntry()
        me.tags.append("test")
        d = me.to_dict()
        assert "entry_id" in d
        assert d["archived"] is False
        assert "test" in d["tags"]


# ─── LearningMemory Tests ─────────────────────────────────────────────
class TestLearningMemory:
    def setup_method(self):
        self.memory = LearningMemory()

    def test_store_lesson(self):
        lesson = Lesson("best_practice", "Test lesson")
        entry = self.memory.store_lesson(lesson)
        assert entry.lesson is not None
        assert "best_practice" in entry.tags
        assert self.memory.entry_count == 1

    def test_store_lesson_with_platform(self):
        lesson = Lesson("best_practice", "Test")
        lesson.platform = "facebook"
        entry = self.memory.store_lesson(lesson)
        assert "facebook" in entry.tags

    def test_store_improvement(self):
        imp = Improvement("Fix this", "critical")
        entry = self.memory.store_improvement(imp)
        assert entry.improvement is not None
        assert "critical" in entry.tags

    def test_store_improvement_with_platform(self):
        imp = Improvement("Fix", "high")
        imp.platform = "linkedin"
        entry = self.memory.store_improvement(imp)
        assert "linkedin" in entry.tags

    def test_store_batch(self):
        lessons = [Lesson("best_practice", f"L{i}") for i in range(3)]
        imps = [Improvement(f"I{i}") for i in range(2)]
        count = self.memory.store_batch(lessons, imps)
        assert count == 5

    def test_search_by_tag(self):
        lesson = Lesson("best_practice", "Test")
        self.memory.store_lesson(lesson)
        results = self.memory.search(tag="best_practice")
        assert len(results) == 1

    def test_search_by_lesson_type(self):
        self.memory.store_lesson(Lesson("best_practice", "A"))
        self.memory.store_lesson(Lesson("mistake", "B"))
        results = self.memory.search(lesson_type="mistake")
        assert len(results) == 1

    def test_search_by_platform(self):
        lesson = Lesson("insight", "Test")
        lesson.platform = "x"
        self.memory.store_lesson(lesson)
        results = self.memory.search(platform="x")
        assert len(results) == 1

    def test_search_excludes_archived(self):
        lesson = Lesson("best_practice", "Test")
        entry = self.memory.store_lesson(lesson)
        self.memory.archive(entry.entry_id)
        results = self.memory.search(tag="best_practice")
        assert len(results) == 0

    def test_get_recent(self):
        for i in range(5):
            self.memory.store_lesson(Lesson("insight", f"L{i}"))
        recent = self.memory.get_recent(3)
        assert len(recent) == 3

    def test_get_by_id(self):
        entry = self.memory.store_lesson(Lesson("insight", "Test"))
        found = self.memory.get_by_id(entry.entry_id)
        assert found is not None
        assert found.entry_id == entry.entry_id

    def test_get_by_id_not_found(self):
        assert self.memory.get_by_id("nonexistent") is None

    def test_archive(self):
        entry = self.memory.store_lesson(Lesson("insight", "Test"))
        assert self.memory.archive(entry.entry_id) is True
        assert self.memory.entry_count == 0

    def test_archive_nonexistent(self):
        assert self.memory.archive("nonexistent") is False

    def test_get_stats(self):
        self.memory.store_lesson(Lesson("best_practice", "A"))
        self.memory.store_improvement(Improvement("B"))
        stats = self.memory.get_stats()
        assert stats["total"] == 2
        assert stats["active"] == 2
        assert stats["lessons"] == 1
        assert stats["improvements"] == 1

    def test_max_entries_overflow(self):
        memory = LearningMemory(max_entries=5)
        for i in range(10):
            memory.store_lesson(Lesson("insight", f"L{i}"))
        assert memory.entry_count == 5

    def test_search_limit(self):
        for i in range(20):
            self.memory.store_lesson(Lesson("insight", f"L{i}"))
        results = self.memory.search(limit=5)
        assert len(results) == 5

    def test_entry_count_archived_excluded(self):
        e1 = self.memory.store_lesson(Lesson("insight", "A"))
        self.memory.store_lesson(Lesson("insight", "B"))
        self.memory.archive(e1.entry_id)
        assert self.memory.entry_count == 1


# ─── ConfidenceRecord Tests ───────────────────────────────────────────
class TestConfidenceRecord:
    def test_create_default(self):
        cr = ConfidenceRecord()
        assert cr.metric_name == ""
        assert cr.confidence == 0.0
        assert cr.reliability == 0.5

    def test_to_dict(self):
        cr = ConfidenceRecord("likes", 0.85)
        cr.reliability = 0.9
        d = cr.to_dict()
        assert d["confidence"] == 0.85
        assert d["reliability"] == 0.9


# ─── ConfidenceTracker Tests ──────────────────────────────────────────
class TestConfidenceTracker:
    def setup_method(self):
        self.tracker = ConfidenceTracker()

    def test_record(self):
        rec = self.tracker.record("likes", 0.85, reliability=0.9, source="analytics")
        assert rec.confidence == 0.85
        assert rec.reliability == 0.9
        assert rec.source == "analytics"

    def test_get_current_confidence(self):
        self.tracker.record("likes", 0.7)
        self.tracker.record("likes", 0.9)
        assert self.tracker.get_current_confidence("likes") == 0.9

    def test_get_current_confidence_empty(self):
        assert self.tracker.get_current_confidence("nonexistent") == 0.0

    def test_get_avg_confidence(self):
        self.tracker.record("likes", 0.6)
        self.tracker.record("likes", 0.8)
        avg = self.tracker.get_avg_confidence("likes")
        assert avg == 0.7

    def test_get_avg_confidence_empty(self):
        assert self.tracker.get_avg_confidence("nonexistent") == 0.0

    def test_get_trend_improving(self):
        for c in [0.5, 0.55, 0.6, 0.65, 0.75]:
            self.tracker.record("likes", c)
        assert self.tracker.get_trend("likes") == "improving"

    def test_get_trend_declining(self):
        for c in [0.9, 0.85, 0.8, 0.75, 0.7]:
            self.tracker.record("likes", c)
        assert self.tracker.get_trend("likes") == "declining"

    def test_get_trend_stable(self):
        for c in [0.7, 0.7, 0.7, 0.7]:
            self.tracker.record("likes", c)
        assert self.tracker.get_trend("likes") == "stable"

    def test_get_trend_insufficient_data(self):
        self.tracker.record("likes", 0.7)
        assert self.tracker.get_trend("likes") == "insufficient_data"

    def test_get_all_metrics(self):
        self.tracker.record("likes", 0.5)
        self.tracker.record("shares", 0.6)
        metrics = self.tracker.get_all_metrics()
        assert "likes" in metrics
        assert "shares" in metrics

    def test_get_history(self):
        for i in range(5):
            self.tracker.record("likes", float(i) / 10)
        history = self.tracker.get_history("likes", limit=3)
        assert len(history) == 3

    def test_get_overall_reliability(self):
        self.tracker.record("a", 0.5, reliability=0.8)
        self.tracker.record("b", 0.6, reliability=0.9)
        rel = self.tracker.get_overall_reliability()
        assert rel == 0.85

    def test_get_overall_reliability_empty(self):
        assert self.tracker.get_overall_reliability() == 0.0

    def test_tracking_count(self):
        self.tracker.record("a", 0.5)
        self.tracker.record("b", 0.6)
        assert self.tracker.tracking_count == 2


# ─── LearningMetrics Tests ────────────────────────────────────────────
class TestLearningMetrics:
    def setup_method(self):
        self.metrics = LearningMetrics()

    def test_initial_state(self):
        assert self.metrics.get_score() == 0.0
        assert self.metrics.get_avg_score() == 0.0
        assert self.metrics.get_improvement_rate() == 0.0
        assert self.metrics.get_learning_efficiency() == 0.0

    def test_record_learning_cycle(self):
        self.metrics.record_learning_cycle(signals=10, patterns=5, lessons=3, improvements=2)
        assert self.metrics.get_score() > 0

    def test_record_improvement_outcome_success(self):
        self.metrics.record_learning_cycle(signals=10, patterns=5, lessons=3, improvements=3)
        self.metrics.record_improvement_outcome(True)
        self.metrics.record_improvement_outcome(True)
        self.metrics.record_improvement_outcome(False)
        assert abs(self.metrics.get_improvement_rate() - round(2 / 3, 3)) < 0.001

    def test_get_improvement_rate_zero_improvements(self):
        assert self.metrics.get_improvement_rate() == 0.0

    def test_learning_efficiency(self):
        self.metrics.record_learning_cycle(signals=10, patterns=5, lessons=5, improvements=2)
        eff = self.metrics.get_learning_efficiency()
        assert eff > 0

    def test_learning_efficiency_zero_signals(self):
        assert self.metrics.get_learning_efficiency() == 0.0

    def test_avg_score(self):
        self.metrics.record_learning_cycle(signals=10, patterns=5, lessons=3, improvements=2)
        self.metrics.record_learning_cycle(signals=20, patterns=10, lessons=6, improvements=4)
        avg = self.metrics.get_avg_score()
        assert avg > 0

    def test_summary(self):
        self.metrics.record_learning_cycle(signals=10, patterns=5, lessons=3, improvements=2)
        summary = self.metrics.get_summary()
        assert "total_signals" in summary
        assert "total_patterns" in summary
        assert "total_lessons" in summary
        assert "learning_efficiency" in summary

    def test_reset(self):
        self.metrics.record_learning_cycle(signals=10, patterns=5, lessons=3, improvements=2)
        self.metrics.reset()
        assert self.metrics.get_score() == 0.0
        summary = self.metrics.get_summary()
        assert summary["total_signals"] == 0

    def test_score_calculation_with_zero_signals(self):
        self.metrics.record_learning_cycle(signals=0, patterns=0, lessons=0, improvements=0)
        assert self.metrics.get_score() == 0.0


# ─── Exceptions Tests ─────────────────────────────────────────────────
class TestExceptions:
    def test_learning_error(self):
        with raise_check(LearningError):
            raise LearningError("test")

    def test_signal_collection_error(self):
        assert issubclass(SignalCollectionError, LearningError)

    def test_lesson_generation_error(self):
        assert issubclass(LessonGenerationError, LearningError)

    def test_memory_storage_error(self):
        assert issubclass(MemoryStorageError, LearningError)


# helper
def raise_check(exc_cls):
    import pytest
    return pytest.raises(exc_cls)


# ─── LearningResult Tests ─────────────────────────────────────────────
class TestLearningResult:
    def test_create_default(self):
        lr = LearningResult()
        assert lr.result_id.startswith("lrn_")
        assert lr.lessons == []
        assert lr.mistakes == []
        assert lr.improvements == []
        assert lr.confidence == 0.0
        assert lr.learning_score == 0.0

    def test_to_dict(self):
        lr = LearningResult()
        lr.success_patterns = 2
        lr.failure_patterns = 1
        lr.version = 1
        d = lr.to_dict()
        assert "result_id" in d
        assert d["success_patterns"] == 2
        assert d["failure_patterns"] == 1
        assert d["version"] == 1


# ─── LearningManager Tests ────────────────────────────────────────────
class TestLearningManager:
    def setup_method(self):
        self.manager = LearningManager()

    def _make_signals(self, count=5, platform="", positive=True):
        signals = []
        for i in range(count):
            s = LearningSignal(
                source="analytics",
                signal_type="engagement",
                metric_name="likes",
                value=float(i + 1) if positive else 0.0,
            )
            if not positive:
                s.previous_value = 10.0
            if platform:
                s.platform = platform
            signals.append(s)
        return signals

    def test_run_learning_cycle_empty(self):
        result = self.manager.run_learning_cycle([])
        assert result.result_id.startswith("lrn_")
        assert result.learning_score == 0.0

    def test_run_learning_cycle_with_signals(self):
        signals = self._make_signals(5, platform="facebook")
        result = self.manager.run_learning_cycle(signals)
        assert result.result_id.startswith("lrn_")
        assert isinstance(result.lessons, list)
        assert isinstance(result.improvements, list)
        assert isinstance(result.next_actions, list)

    def test_run_learning_cycle_with_previous(self):
        prev = self._make_signals(3, positive=False)
        curr = self._make_signals(3, positive=True)
        result = self.manager.run_learning_cycle(curr, previous_signals=prev)
        assert result.confidence >= 0.0

    def test_health(self):
        self.manager.run_learning_cycle(self._make_signals(5))
        health = self.manager.get_health()
        assert "total_cycles" in health
        assert "memory_stats" in health
        assert "learning_metrics" in health

    def test_cycle_count(self):
        self.manager.run_learning_cycle([])
        self.manager.run_learning_cycle([])
        assert self.manager.cycle_count == 2

    def test_events_tracked(self):
        self.manager.run_learning_cycle([])
        events = self.manager.events
        assert len(events) == 1
        assert events[0]["event"] == "learning_cycle_completed"

    def test_get_recent_results(self):
        for _ in range(3):
            self.manager.run_learning_cycle([])
        results = self.manager.get_recent_results(2)
        assert len(results) == 2

    def test_learning_cycle_failure_patterns(self):
        signals = []
        for i in range(5):
            s = LearningSignal(source="analytics", signal_type="failure", metric_name="errors", value=0.0)
            s.previous_value = 10.0
            signals.append(s)
        result = self.manager.run_learning_cycle(signals)
        assert result.failure_patterns >= 1
        assert any("failure" in a.lower() or "investigate" in a.lower() for a in result.next_actions)

    def test_learning_cycle_success_patterns(self):
        signals = []
        for i in range(5):
            s = LearningSignal(source="analytics", signal_type="engagement", metric_name="likes", value=float(i + 10))
            s.platform = "linkedin"
            signals.append(s)
        result = self.manager.run_learning_cycle(signals)
        assert result.success_patterns >= 1

    def test_next_actions_no_patterns(self):
        signals = [LearningSignal(metric_name="m", value=1.0)]
        result = self.manager.run_learning_cycle(signals)
        assert len(result.next_actions) >= 1

    def test_learning_score_after_cycle(self):
        signals = self._make_signals(10, platform="x")
        result = self.manager.run_learning_cycle(signals)
        assert result.learning_score >= 0.0

    def test_manager_reuses_components(self):
        assert self.manager.feedback_collector is not None
        assert self.manager.comparator is not None
        assert self.manager.pattern_detector is not None
        assert self.manager.lesson_generator is not None
        assert self.manager.improvement_planner is not None
        assert self.manager.learning_memory is not None
        assert self.manager.confidence_tracker is not None
        assert self.manager.metrics is not None

    def test_memory_populated_after_cycle(self):
        signals = self._make_signals(5, platform="facebook")
        self.manager.run_learning_cycle(signals)
        stats = self.manager.learning_memory.get_stats()
        assert stats["total"] > 0

    def test_confidence_tracker_populated(self):
        prev = self._make_signals(3, positive=False)
        curr = self._make_signals(3, positive=True)
        self.manager.run_learning_cycle(curr, previous_signals=prev)
        metrics = self.manager.confidence_tracker.get_all_metrics()
        assert len(metrics) > 0


# ─── Cross-module Integration Tests ───────────────────────────────────
class TestLearningEngineIntegration:
    def test_full_pipeline(self):
        """Test complete pipeline: Signal → Collect → Detect → Lesson → Improve → Store."""
        collector = FeedbackCollector()
        fs = FeedbackSource(source_id="analytics1", name="Analytics", source_type="analytics")
        fs.fetcher = lambda: [
            {"type": "engagement", "metric": "likes", "value": 100.0, "platform": "facebook"},
            {"type": "engagement", "metric": "likes", "value": 120.0, "platform": "facebook"},
            {"type": "engagement", "metric": "likes", "value": 110.0, "platform": "facebook"},
            {"type": "engagement", "metric": "likes", "value": 130.0, "platform": "facebook"},
            {"type": "engagement", "metric": "likes", "value": 140.0, "platform": "facebook"},
        ]
        collector.register_source(fs)
        signals = collector.collect_from_source("analytics1")
        assert len(signals) == 5

        detector = PatternDetector()
        patterns = detector.detect(signals)
        assert len(patterns) > 0

        gen = LessonGenerator()
        lessons = gen.generate(patterns)
        assert len(lessons) > 0

        planner = ImprovementPlanner()
        improvements = planner.plan_from_lessons(lessons)
        assert len(improvements) > 0

        memory = LearningMemory()
        for lesson in lessons:
            memory.store_lesson(lesson)
        for imp in improvements:
            memory.store_improvement(imp)
        stats = memory.get_stats()
        assert stats["total"] == len(lessons) + len(improvements)

    def test_comparator_to_patterns_to_lessons(self):
        """Test Comparator → PatternDetector → LessonGenerator pipeline."""
        comp = PerformanceComparator()
        prev = [LearningSignal(metric_name="reach", value=500.0)]
        curr = [LearningSignal(metric_name="reach", value=800.0)]
        comp.compare_signals(prev, curr)

        signals = curr + prev
        detector = PatternDetector()
        patterns = detector.detect(signals)

        gen = LessonGenerator()
        lessons = gen.generate(patterns)
        assert isinstance(lessons, list)

    def test_full_manager_cycle_with_feedback(self):
        """Test LearningManager with actual FeedbackCollector data."""
        manager = LearningManager()
        manager.feedback_collector.register_source(
            FeedbackSource(source_id="s1", name="Test", source_type="analytics")
        )
        manager.feedback_collector._sources["s1"].fetcher = lambda: [
            {"type": "engagement", "metric": "likes", "value": float(i), "platform": "x"}
            for i in range(5)
        ]
        signals = manager.feedback_collector.collect_from_source("s1")
        assert len(signals) == 5

        result = manager.run_learning_cycle(signals)
        assert result.result_id.startswith("lrn_")
        assert manager.cycle_count == 1
        assert len(manager.events) == 1

    def test_confidence_and_metrics_integration(self):
        """Test that ConfidenceTracker and LearningMetrics integrate with Manager."""
        manager = LearningManager()
        prev = [
            LearningSignal(metric_name="likes", value=50.0),
            LearningSignal(metric_name="shares", value=10.0),
        ]
        curr = [
            LearningSignal(metric_name="likes", value=75.0),
            LearningSignal(metric_name="shares", value=8.0),
        ]
        result = manager.run_learning_cycle(curr, previous_signals=prev)
        assert result.confidence >= 0.0
        metrics_summary = manager.metrics.get_summary()
        assert metrics_summary["total_signals"] == 2

    def test_memory_search_after_learning(self):
        """Test that memory search works after learning cycles."""
        manager = LearningManager()
        signals = [
            LearningSignal(source="analytics", signal_type="engagement",
                          metric_name="likes", value=float(i + 1))
            for i in range(5)
        ]
        for s in signals:
            s.platform = "facebook"
        manager.run_learning_cycle(signals)

        results = manager.learning_memory.search(platform="facebook")
        assert len(results) > 0

    def test_lesson_types_all_covered(self):
        """Verify all lesson types can be generated."""
        gen = LessonGenerator()
        types_found = set()
        for ptype in ["success", "failure", "repeated", "seasonal"]:
            p = DetectedPattern(ptype, f"Test {ptype}")
            p.confidence = 0.8
            p.frequency = 5
            p.platform = "test"
            p.tags = ["test"]
            lessons = gen.generate([p])
            for l in lessons:
                types_found.add(l.lesson_type)
        assert "best_practice" in types_found
        assert "mistake" in types_found
        assert "insight" in types_found
        assert "recommendation" in types_found

    def test_improvement_priorities_all_covered(self):
        """Verify all priority levels are reachable."""
        planner = ImprovementPlanner()
        for ltype in ["mistake", "best_practice", "warning", "insight"]:
            lesson = Lesson(ltype, f"Test {ltype}")
            planner.plan_from_lessons([lesson])
        priorities = set(i.priority for i in planner.prioritize())
        assert "critical" in priorities
        assert "high" in priorities
        assert "medium" in priorities
        assert "low" in priorities
