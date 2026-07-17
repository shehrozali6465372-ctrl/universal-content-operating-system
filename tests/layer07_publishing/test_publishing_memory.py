"""Tests for Layer 7 Module 8 — Publishing Memory."""
import time
from layers.layer07_publishing.modules.publishing_memory.publish_history import PublishHistory, PublishRecord
from layers.layer07_publishing.modules.publishing_memory.platform_memory import PlatformMemory
from layers.layer07_publishing.modules.publishing_memory.schedule_memory import ScheduleMemory
from layers.layer07_publishing.modules.publishing_memory.audience_memory import AudienceMemory
from layers.layer07_publishing.modules.publishing_memory.performance_memory import PerformanceMemory, PerformanceSnapshot
from layers.layer07_publishing.modules.publishing_memory.publish_failure_memory import PublishFailureMemory, FailureEntry
from layers.layer07_publishing.modules.publishing_memory.pattern_learner import PatternLearner, Pattern
from layers.layer07_publishing.modules.publishing_memory.memory_search import MemorySearch, SearchFilter
from layers.layer07_publishing.modules.publishing_memory.memory_retention import MemoryRetention, RetentionPolicy, ArchiveRecord
from layers.layer07_publishing.modules.publishing_memory.publishing_memory_manager import (
    PublishingMemoryManager, PublishingMemoryResult,
)
from layers.layer07_publishing.modules.publishing_memory.exceptions import (
    MemoryError, StorageError, SearchError,
)


def _make_record(platform="facebook", content_type="post", tags=None):
    r = PublishRecord(platform=platform, post_id=f"p_{platform}_{int(time.time()*1000)%10000}")
    r.content_type = content_type
    r.content_summary = "test content for publishing"
    r.tags = tags or []
    r.success = True
    return r


# ─── PublishHistory Tests ────────────────────────────────────────────
class TestPublishRecord:
    def test_create(self):
        r = PublishRecord("facebook", "p1", "c1")
        assert r.record_id.startswith("pm_")
        assert r.platform == "facebook"
        assert r.post_id == "p1"
        assert r.success is True

    def test_get_hour(self):
        r = PublishRecord()
        assert 0 <= r.get_hour() <= 23

    def test_get_weekday(self):
        r = PublishRecord()
        assert 0 <= r.get_weekday() <= 6

    def test_to_dict(self):
        r = PublishRecord("fb", "p1", "c1")
        r.tags = ["ai"]
        d = r.to_dict()
        assert d["platform"] == "fb"
        assert "ai" in d["tags"]


class TestPublishHistory:
    def setup_method(self):
        self.history = PublishHistory()

    def test_record(self):
        r = _make_record("facebook")
        self.history.record(r)
        assert self.history.get_count() == 1

    def test_get_all(self):
        self.history.record(_make_record("fb"))
        self.history.record(_make_record("li"))
        assert len(self.history.get_all()) == 2

    def test_get_by_platform(self):
        self.history.record(_make_record("fb"))
        self.history.record(_make_record("li"))
        self.history.record(_make_record("fb"))
        assert len(self.history.get_by_platform("fb")) == 2

    def test_get_by_content_id(self):
        r = _make_record()
        r.content_id = "c1"
        self.history.record(r)
        assert len(self.history.get_by_content_id("c1")) == 1

    def test_get_by_status(self):
        r = _make_record()
        r.status = "scheduled"
        self.history.record(r)
        assert len(self.history.get_by_status("scheduled")) == 1

    def test_get_recent(self):
        for i in range(10):
            self.history.record(_make_record())
        assert len(self.history.get_recent(3)) == 3

    def test_get_platform_count(self):
        self.history.record(_make_record("fb"))
        self.history.record(_make_record("fb"))
        assert self.history.get_platform_count("fb") == 2

    def test_get_success_rate(self):
        for _ in range(8):
            self.history.record(_make_record())
        r = _make_record()
        r.success = False
        self.history.record(r)
        assert self.history.get_success_rate() > 0.8

    def test_max_records_overflow(self):
        h = PublishHistory(max_records=5)
        for _ in range(10):
            h.record(_make_record())
        assert h.get_count() <= 5


# ─── PlatformMemory Tests ────────────────────────────────────────────
class TestPlatformMemory:
    def setup_method(self):
        self.pm = PlatformMemory()

    def test_observe(self):
        profile = self.pm.observe(_make_record("facebook"))
        assert profile.platform == "facebook"
        assert profile.total_publishes == 1

    def test_observe_multiple(self):
        self.pm.observe(_make_record("fb"))
        self.pm.observe(_make_record("fb"))
        self.pm.observe(_make_record("li"))
        assert self.pm.platform_count == 2
        fb = self.pm.get_profile("fb")
        assert fb.total_publishes == 2

    def test_get_profile(self):
        self.pm.observe(_make_record("fb"))
        assert self.pm.get_profile("fb") is not None
        assert self.pm.get_profile("tw") is None

    def test_get_all_profiles(self):
        self.pm.observe(_make_record("fb"))
        self.pm.observe(_make_record("li"))
        assert len(self.pm.get_all_profiles()) == 2

    def test_get_best_platform(self):
        for _ in range(5):
            self.pm.observe(_make_record("fb"))
        for _ in range(2):
            self.pm.observe(_make_record("li"))
        assert self.pm.get_best_platform() == "fb"

    def test_get_records(self):
        self.pm.observe(_make_record("fb"))
        assert len(self.pm.get_records("fb")) == 1

    def test_success_rate(self):
        for _ in range(3):
            self.pm.observe(_make_record("fb"))
        assert self.pm.get_profile("fb").success_rate == 1.0


# ─── ScheduleMemory Tests ────────────────────────────────────────────
class TestScheduleMemory:
    def setup_method(self):
        self.sm = ScheduleMemory()

    def test_observe(self):
        r = _make_record()
        self.sm.observe(r)
        assert self.sm.total_count == 1

    def test_get_insight(self):
        for _ in range(10):
            r = _make_record()
            self.sm.observe(r)
        insight = self.sm.get_insight()
        assert insight.total_data_points == 10
        assert len(insight.best_hours) <= 3

    def test_hour_distribution(self):
        for _ in range(5):
            self.sm.observe(_make_record())
        dist = self.sm.get_hour_distribution()
        assert isinstance(dist, dict)

    def test_weekday_distribution(self):
        for _ in range(5):
            self.sm.observe(_make_record())
        dist = self.sm.get_weekday_distribution()
        assert isinstance(dist, dict)

    def test_insight_to_dict(self):
        for _ in range(3):
            self.sm.observe(_make_record())
        d = self.sm.get_insight().to_dict()
        assert "best_hours" in d
        assert "best_weekdays" in d

    def test_confidence(self):
        for _ in range(150):
            self.sm.observe(_make_record())
        insight = self.sm.get_insight()
        assert insight.confidence == 1.0


# ─── AudienceMemory Tests ────────────────────────────────────────────
class TestAudienceMemory:
    def setup_method(self):
        self.am = AudienceMemory()

    def test_observe(self):
        self.am.observe("post", "fb", 5.0)
        assert self.am.history_count == 1

    def test_observe_multiple(self):
        self.am.observe("post", "fb", 3.0)
        self.am.observe("post", "fb", 5.0)
        self.am.observe("article", "li", 8.0)
        assert self.am.segment_count == 2

    def test_get_segment(self):
        self.am.observe("post", "fb", 4.0)
        seg = self.am.get_segment("fb", "post")
        assert seg.sample_size == 1
        assert seg.avg_engagement_rate == 4.0

    def test_get_all_segments(self):
        self.am.observe("post", "fb", 3.0)
        self.am.observe("article", "li", 7.0)
        assert len(self.am.get_all_segments()) == 2

    def test_get_best_content_type(self):
        self.am.observe("post", "fb", 2.0)
        self.am.observe("article", "li", 8.0)
        assert self.am.get_best_content_type() == "article"

    def test_get_avg_engagement(self):
        self.am.observe("post", "fb", 3.0)
        self.am.observe("post", "fb", 5.0)
        assert self.am.get_avg_engagement("post") == 4.0

    def test_segment_to_dict(self):
        self.am.observe("post", "fb", 4.0)
        seg = self.am.get_segment("fb", "post")
        d = seg.to_dict()
        assert "sample_size" in d


# ─── PerformanceMemory Tests ─────────────────────────────────────────
class TestPerformanceMemory:
    def setup_method(self):
        self.pm = PerformanceMemory()

    def test_record(self):
        s = PerformanceSnapshot("fb", "p1")
        s.reach = 1000
        self.pm.record(s)
        assert self.pm.snapshot_count == 1

    def test_get_avg_reach(self):
        s1 = PerformanceSnapshot("fb", "p1")
        s1.reach = 1000
        s2 = PerformanceSnapshot("fb", "p2")
        s2.reach = 2000
        self.pm.record(s1)
        self.pm.record(s2)
        assert self.pm.get_avg_reach("fb") == 1500.0

    def test_get_avg_ctr(self):
        s = PerformanceSnapshot("fb", "p1")
        s.ctr = 3.5
        self.pm.record(s)
        assert self.pm.get_avg_ctr("fb") == 3.5

    def test_get_total_revenue(self):
        s1 = PerformanceSnapshot("fb", "p1")
        s1.revenue = 100
        s2 = PerformanceSnapshot("li", "p2")
        s2.revenue = 200
        self.pm.record(s1)
        self.pm.record(s2)
        assert self.pm.get_total_revenue() == 300

    def test_get_roi(self):
        s = PerformanceSnapshot("fb", "p1")
        s.revenue = 200
        s.cost = 100
        self.pm.record(s)
        assert self.pm.get_roi() == 1.0

    def test_get_best_platform(self):
        s1 = PerformanceSnapshot("fb", "p1")
        s1.reach = 5000
        s2 = PerformanceSnapshot("li", "p2")
        s2.reach = 1000
        self.pm.record(s1)
        self.pm.record(s2)
        assert self.pm.get_best_platform("reach") == "fb"

    def test_get_snapshots(self):
        self.pm.record(PerformanceSnapshot("fb", "p1"))
        self.pm.record(PerformanceSnapshot("li", "p2"))
        assert len(self.pm.get_snapshots("fb")) == 1
        assert len(self.pm.get_snapshots()) == 2

    def test_snapshot_to_dict(self):
        s = PerformanceSnapshot("fb", "p1")
        d = s.to_dict()
        assert d["platform"] == "fb"


# ─── PublishFailureMemory Tests ──────────────────────────────────────
class TestPublishFailureMemory:
    def setup_method(self):
        self.fm = PublishFailureMemory()

    def test_record(self):
        e = FailureEntry("fb", "network")
        self.fm.record(e)
        assert self.fm.get_total_failures() == 1

    def test_get_error_frequency(self):
        self.fm.record(FailureEntry("fb", "network"))
        self.fm.record(FailureEntry("fb", "network"))
        self.fm.record(FailureEntry("li", "auth"))
        freq = self.fm.get_error_frequency()
        assert freq["network"] == 2

    def test_get_recovery_effectiveness(self):
        e1 = FailureEntry("fb", "network")
        e1.recovered = True
        e1.recovery_action = "retry"
        self.fm.record(e1)
        e2 = FailureEntry("fb", "network")
        e2.recovered = False
        e2.recovery_action = "retry"
        self.fm.record(e2)
        eff = self.fm.get_recovery_effectiveness()
        assert eff["retry"] == 0.5

    def test_get_platform_failures(self):
        self.fm.record(FailureEntry("fb", "network"))
        self.fm.record(FailureEntry("fb", "auth"))
        self.fm.record(FailureEntry("li", "network"))
        pf = self.fm.get_platform_failures()
        assert pf["fb"] == 2

    def test_get_entries_filter(self):
        self.fm.record(FailureEntry("fb", "network"))
        self.fm.record(FailureEntry("li", "auth"))
        assert len(self.fm.get_entries(platform="fb")) == 1
        assert len(self.fm.get_entries(error_type="auth")) == 1

    def test_get_recovery_rate(self):
        e1 = FailureEntry("fb", "e")
        e1.recovered = True
        self.fm.record(e1)
        assert self.fm.get_recovery_rate() == 1.0

    def test_get_recovery_rate_empty(self):
        assert self.fm.get_recovery_rate() == 1.0


# ─── PatternLearner Tests ────────────────────────────────────────────
class TestPatternLearner:
    def setup_method(self):
        self.pl = PatternLearner()

    def test_detect_patterns(self):
        records = [_make_record("fb", "post", ["ai"]) for _ in range(5)]
        patterns = self.pl.detect_patterns(records)
        assert len(patterns) > 0

    def test_detect_platform_pattern(self):
        records = [_make_record("fb") for _ in range(5)]
        records += [_make_record("li") for _ in range(2)]
        patterns = self.pl.detect_patterns(records)
        platform_patterns = [p for p in patterns if p.pattern_type == "platform_preference"]
        assert len(platform_patterns) > 0
        assert platform_patterns[0].frequency == 5

    def test_detect_content_type_pattern(self):
        records = [_make_record("fb", "article") for _ in range(5)]
        records += [_make_record("fb", "post") for _ in range(2)]
        patterns = self.pl.detect_patterns(records)
        ct_patterns = [p for p in patterns if p.pattern_type == "content_type_preference"]
        assert len(ct_patterns) > 0

    def test_detect_tag_patterns(self):
        records = [_make_record("fb", "post", ["ai", "tech"]) for _ in range(5)]
        patterns = self.pl.detect_patterns(records)
        tag_patterns = [p for p in patterns if p.pattern_type == "tag_preference"]
        assert len(tag_patterns) > 0

    def test_insufficient_data(self):
        records = [_make_record("fb") for _ in range(2)]
        patterns = self.pl.detect_patterns(records)
        assert len(patterns) == 0

    def test_get_recommendations(self):
        records = [_make_record("fb", "post", ["ai"]) for _ in range(10)]
        recs = self.pl.get_recommendations(records)
        assert len(recs) > 0
        assert recs[0]["confidence"] >= 0.5

    def test_get_best_combination(self):
        records = [_make_record("fb", "article") for _ in range(5)]
        records += [_make_record("li", "post") for _ in range(3)]
        combo = self.pl.get_best_combination(records)
        assert combo["platform"] == "fb"
        assert combo["content_type"] == "article"

    def test_get_best_combination_empty(self):
        combo = self.pl.get_best_combination([])
        assert combo["platform"] == ""

    def test_pattern_to_dict(self):
        p = Pattern("test", "description")
        d = p.to_dict()
        assert d["pattern_type"] == "test"


# ─── MemorySearch Tests ──────────────────────────────────────────────
class TestSearchFilter:
    def test_create(self):
        sf = SearchFilter()
        assert sf.platform == ""
        sf.platform = "fb"
        d = sf.to_dict()
        assert d["platform"] == "fb"


class TestMemorySearch:
    def setup_method(self):
        self.history = PublishHistory()
        for i in range(10):
            r = _make_record("fb" if i % 2 == 0 else "li", "post" if i % 3 == 0 else "article")
            r.tags = ["ai"] if i < 5 else ["tech"]
            self.history.record(r)
        self.search = MemorySearch(self.history)

    def test_search_all(self):
        sf = SearchFilter()
        result = self.search.search(sf)
        assert result.total_matches == 10

    def test_search_by_platform(self):
        sf = SearchFilter()
        sf.platform = "fb"
        result = self.search.search(sf)
        assert result.total_matches == 5

    def test_search_by_content_type(self):
        sf = SearchFilter()
        sf.content_type = "post"
        result = self.search.search(sf)
        assert result.total_matches > 0

    def test_search_by_tags(self):
        sf = SearchFilter()
        sf.tags = ["ai"]
        result = self.search.search(sf)
        assert result.total_matches == 5

    def test_search_by_text(self):
        sf = SearchFilter()
        sf.text_query = "test"
        result = self.search.search(sf)
        assert result.total_matches == 10

    def test_find_similar(self):
        records = self.history.get_all()
        similar = self.search.find_similar(records[0], limit=3)
        assert len(similar) <= 3

    def test_search_count(self):
        self.search.search(SearchFilter())
        self.search.search(SearchFilter())
        assert self.search.search_count == 2

    def test_result_to_dict(self):
        result = self.search.search(SearchFilter())
        d = result.to_dict()
        assert "total_matches" in d


# ─── MemoryRetention Tests ───────────────────────────────────────────
class TestRetentionPolicy:
    def test_create(self):
        p = RetentionPolicy(max_records=100)
        assert p.max_records == 100
        d = p.to_dict()
        assert d["max_records"] == 100


class TestMemoryRetention:
    def setup_method(self):
        self.ret = MemoryRetention(RetentionPolicy(retention_days=1))

    def test_cleanup(self):
        h = PublishHistory()
        r = _make_record()
        r.published_at = time.time() - (2 * 86400)  # 2 days ago
        h.record(r)
        removed = self.ret.cleanup(h)
        assert removed >= 1

    def test_archive(self):
        records = [_make_record() for _ in range(5)]
        for r in records:
            r.published_at = time.time() - (100 * 86400)
        archived = self.ret.archive(records)
        assert archived == 5

    def test_should_compress(self):
        r = _make_record()
        r.published_at = time.time() - (40 * 86400)
        assert self.ret.should_compress(r) is True

    def test_should_not_compress_recent(self):
        r = _make_record()
        r.published_at = time.time() - (5 * 86400)
        assert self.ret.should_compress(r) is False

    def test_get_archives(self):
        records = [_make_record()]
        records[0].published_at = time.time() - (100 * 86400)
        self.ret.archive(records)
        assert len(self.ret.get_archives()) == 1

    def test_archive_record_to_dict(self):
        r = _make_record("fb")
        ar = ArchiveRecord(r)
        d = ar.to_dict()
        assert d["platform"] == "fb"


# ─── PublishingMemoryManager Tests ───────────────────────────────────
class TestPublishingMemoryResult:
    def test_create(self):
        r = PublishingMemoryResult()
        assert r.result_id.startswith("pmr_")
        r.best_platform = "fb"
        d = r.to_dict()
        assert d["best_platform"] == "fb"


class TestPublishingMemoryManager:
    def setup_method(self):
        self.mgr = PublishingMemoryManager()

    def test_store(self):
        rec = _make_record("fb")
        result = self.mgr.store(rec)
        assert result.platform == "fb"
        assert self.mgr.history.get_count() == 1

    def test_store_with_engagement(self):
        rec = _make_record("fb", "post")
        self.mgr.store_with_engagement(rec, engagement_rate=5.0)
        assert self.mgr.history.get_count() == 1
        assert self.mgr.audience_memory.history_count == 1

    def test_store_performance(self):
        s = PerformanceSnapshot("fb", "p1")
        s.reach = 1000
        self.mgr.store_performance(s)
        assert self.mgr.performance_memory.snapshot_count == 1

    def test_store_failure(self):
        e = FailureEntry("fb", "network")
        self.mgr.store_failure(e)
        assert self.mgr.failure_memory.get_total_failures() == 1

    def test_recommend_empty(self):
        result = self.mgr.recommend()
        assert result.confidence == 0.0
        assert "No history" in result.recommendation

    def test_recommend_with_data(self):
        for i in range(20):
            rec = _make_record("fb" if i % 3 == 0 else "li", "post" if i % 2 == 0 else "article")
            self.mgr.store_with_engagement(rec, engagement_rate=float(i))
        result = self.mgr.recommend()
        assert result.confidence > 0
        assert result.best_platform != ""
        assert len(result.recommendation) > 0

    def test_search(self):
        for _ in range(5):
            self.mgr.store(_make_record("fb"))
        sf = SearchFilter()
        sf.platform = "fb"
        sr = self.mgr.search(sf)
        assert sr.total_matches == 5

    def test_get_learning_signals_empty(self):
        signals = self.mgr.get_learning_signals()
        assert signals["available"] is False

    def test_get_learning_signals(self):
        for _ in range(5):
            self.mgr.store(_make_record("fb"))
        signals = self.mgr.get_learning_signals()
        assert signals["available"] is True
        assert signals["total_publishes"] == 5

    def test_events_tracked(self):
        for _ in range(5):
            self.mgr.store(_make_record("fb"))
        self.mgr.recommend()
        assert len(self.mgr.events) >= 1

    def test_platform_memory_integrated(self):
        self.mgr.store(_make_record("fb"))
        profile = self.mgr.platform_memory.get_profile("fb")
        assert profile is not None
        assert profile.total_publishes == 1


# ─── Exceptions Tests ────────────────────────────────────────────────
class TestExceptions:
    def test_hierarchy(self):
        assert issubclass(MemoryError, Exception)
        assert issubclass(StorageError, MemoryError)
        assert issubclass(SearchError, MemoryError)

    def test_message(self):
        err = StorageError("storage failed")
        assert str(err) == "storage failed"
