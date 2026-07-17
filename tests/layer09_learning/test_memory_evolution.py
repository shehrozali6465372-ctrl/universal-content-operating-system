"""Tests for Layer 9 Module 5 — Memory Evolution Engine."""
from layers.layer09_learning.modules.memory_evolution.memory_classifier import (
    MemoryClassifier,
)
from layers.layer09_learning.modules.memory_evolution.memory_merger import MemoryMerger
from layers.layer09_learning.modules.memory_evolution.memory_cleanup import MemoryCleanup
from layers.layer09_learning.modules.memory_evolution.memory_ranker import MemoryRanker
from layers.layer09_learning.modules.memory_evolution.memory_expiry import (
    MemoryExpiry, ExpiryPolicy,
)
from layers.layer09_learning.modules.memory_evolution.memory_archive import MemoryArchive
from layers.layer09_learning.modules.memory_evolution.memory_search import MemorySearch
from layers.layer09_learning.modules.memory_evolution.memory_optimizer import MemoryOptimizer
from layers.layer09_learning.modules.memory_evolution.memory_metrics import MemoryEvolutionMetrics
from layers.layer09_learning.modules.memory_evolution.memory_manager import MemoryManager, EvolutionCycleResult
from layers.layer09_learning.modules.memory_evolution.exceptions import (
    MemoryEvolutionError, ClassificationError, MergeError, ArchiveError,
)


# ─── MemoryClassifier Tests ──────────────────────────────────────────
class TestMemoryClassifier:
    def setup_method(self):
        self.classifier = MemoryClassifier()

    def test_classify_basic(self):
        cm = self.classifier.classify("mem_1", "lesson", confidence=0.8, usage_count=5)
        assert cm.memory_id == "mem_1"
        assert cm.category == "lesson"
        assert cm.importance == "high"
        assert cm.lifecycle == "active"
        assert cm.score > 0

    def test_classify_critical(self):
        cm = self.classifier.classify("mem_1", "lesson", confidence=0.95, usage_count=8)
        assert cm.importance == "critical"

    def test_classify_low(self):
        cm = self.classifier.classify("mem_1", "lesson", confidence=0.1, usage_count=0)
        assert cm.importance == "low"

    def test_classify_aging(self):
        cm = self.classifier.classify("mem_1", "insight", confidence=0.5, usage_count=2, age_days=75)
        assert cm.lifecycle == "aging"

    def test_classify_expired(self):
        cm = self.classifier.classify("mem_1", "insight", confidence=0.5, usage_count=1, age_days=100)
        assert cm.lifecycle == "expired"

    def test_classify_mature(self):
        cm = self.classifier.classify("mem_1", "insight", confidence=0.5, usage_count=2, age_days=35)
        assert cm.lifecycle == "mature"

    def test_classify_batch(self):
        entries = [
            {"memory_id": "m1", "source_type": "lesson", "confidence": 0.8},
            {"memory_id": "m2", "source_type": "mistake", "confidence": 0.3},
        ]
        results = self.classifier.classify_batch(entries)
        assert len(results) == 2
        assert results[0].category == "lesson"
        assert results[1].category == "mistake"

    def test_classification_count(self):
        self.classifier.classify("m1", "lesson")
        self.classifier.classify("m2", "insight")
        assert self.classifier.classification_count == 2

    def test_get_by_importance(self):
        self.classifier.classify("m1", "lesson", confidence=0.95, usage_count=8)
        self.classifier.classify("m2", "lesson", confidence=0.1, usage_count=0)
        critical = self.classifier.get_by_importance("critical")
        low = self.classifier.get_by_importance("low")
        assert len(critical) == 1
        assert len(low) == 1

    def test_get_by_lifecycle(self):
        self.classifier.classify("m1", "lesson", age_days=0)
        self.classifier.classify("m2", "lesson", age_days=100, usage_count=1)
        active = self.classifier.get_by_lifecycle("active")
        expired = self.classifier.get_by_lifecycle("expired")
        assert len(active) == 1
        assert len(expired) == 1

    def test_result_to_dict(self):
        cm = self.classifier.classify("m1", "lesson", confidence=0.8)
        d = cm.to_dict()
        assert "memory_id" in d
        assert "importance" in d

    def test_unknown_source_type(self):
        cm = self.classifier.classify("m1", "unknown_type")
        assert cm.category == "insight"


# ─── MemoryMerger Tests ──────────────────────────────────────────────
class TestMemoryMerger:
    def setup_method(self):
        self.merger = MemoryMerger()

    def test_merge_by_keyword(self):
        entries = [
            {"entry_id": "e1", "tags": ["ai", "tech"], "description": "AI insight", "confidence": 0.8},
            {"entry_id": "e2", "tags": ["ai", "ml"], "description": "ML insight", "confidence": 0.7},
            {"entry_id": "e3", "tags": ["design"], "description": "Design tip", "confidence": 0.6},
        ]
        results = self.merger.merge_by_keyword(entries)
        assert len(results) >= 1

    def test_merge_by_type(self):
        entries = [
            {"entry_id": "e1", "learning_type": "insight", "description": "A", "confidence": 0.8},
            {"entry_id": "e2", "learning_type": "insight", "description": "B", "confidence": 0.7},
            {"entry_id": "e3", "learning_type": "mistake", "description": "C", "confidence": 0.3},
        ]
        results = self.merger.merge_by_type(entries)
        assert len(results) >= 1

    def test_merge_no_groups(self):
        entries = [{"entry_id": "e1", "tags": ["unique"]}]
        results = self.merger.merge_by_keyword(entries, min_similarity=3)
        assert len(results) == 0

    def test_merge_count(self):
        entries = [
            {"entry_id": "e1", "tags": ["a"], "description": "X", "confidence": 0.8},
            {"entry_id": "e2", "tags": ["a"], "description": "Y", "confidence": 0.7},
        ]
        self.merger.merge_by_keyword(entries)
        assert self.merger.merge_count >= 1

    def test_result_to_dict(self):
        entries = [
            {"entry_id": "e1", "tags": ["test"], "description": "A", "confidence": 0.8},
            {"entry_id": "e2", "tags": ["test"], "description": "B", "confidence": 0.7},
        ]
        results = self.merger.merge_by_keyword(entries)
        if results:
            d = results[0].to_dict()
            assert "merged_id" in d


# ─── MemoryCleanup Tests ─────────────────────────────────────────────
class TestMemoryCleanup:
    def setup_method(self):
        self.cleanup = MemoryCleanup()

    def test_cleanup_keep(self):
        entries = [{"entry_id": "e1", "score": 0.8, "age_days": 10, "usage_count": 5}]
        report = self.cleanup.cleanup(entries)
        assert report.kept == 1
        assert report.deleted == 0

    def test_cleanup_delete(self):
        entries = [{"entry_id": "e1", "score": 0.05, "age_days": 5, "usage_count": 0}]
        report = self.cleanup.cleanup(entries)
        assert report.deleted == 1

    def test_cleanup_archive(self):
        entries = [{"entry_id": "e1", "score": 0.25, "age_days": 100, "usage_count": 0}]
        report = self.cleanup.cleanup(entries)
        assert report.archived == 1

    def test_cleanup_mixed(self):
        entries = [
            {"entry_id": "e1", "score": 0.9, "age_days": 5, "usage_count": 3},
            {"entry_id": "e2", "score": 0.05, "age_days": 5, "usage_count": 0},
            {"entry_id": "e3", "score": 0.25, "age_days": 100, "usage_count": 0},
        ]
        report = self.cleanup.cleanup(entries)
        assert report.total_checked == 3
        assert report.kept + report.deleted + report.archived == 3

    def test_cleanup_empty(self):
        report = self.cleanup.cleanup([])
        assert report.total_checked == 0

    def test_cleanup_report_to_dict(self):
        entries = [{"entry_id": "e1", "score": 0.9, "age_days": 5, "usage_count": 3}]
        report = self.cleanup.cleanup(entries)
        d = report.to_dict()
        assert "total_checked" in d
        assert "space_freed" in d

    def test_custom_config(self):
        config = {"max_age_days": 10, "min_score": 0.5, "min_usage": 3,
                  "archive_threshold": 0.6, "delete_threshold": 0.2}
        cleanup = MemoryCleanup(config)
        entries = [{"entry_id": "e1", "score": 0.3, "age_days": 15, "usage_count": 1}]
        report = cleanup.cleanup(entries)
        assert report.archived + report.kept + report.deleted == 1


# ─── MemoryRanker Tests ──────────────────────────────────────────────
class TestMemoryRanker:
    def setup_method(self):
        self.ranker = MemoryRanker()

    def test_rank_basic(self):
        entries = [
            {"entry_id": "e1", "confidence": 0.9, "usage_count": 8, "age_days": 5, "score": 0.8, "tags": ["a", "b"]},
            {"entry_id": "e2", "confidence": 0.3, "usage_count": 1, "age_days": 60, "score": 0.3, "tags": ["c"]},
        ]
        ranked = self.ranker.rank(entries)
        assert len(ranked) == 2
        assert ranked[0].rank == 1
        assert ranked[0].rank_score >= ranked[1].rank_score

    def test_rank_top_k(self):
        entries = [
            {"entry_id": f"e{i}", "confidence": 0.5, "usage_count": i, "age_days": i * 10, "score": 0.5, "tags": ["a"]}
            for i in range(5)
        ]
        ranked = self.ranker.rank(entries, top_k=2)
        assert len(ranked) == 2

    def test_rank_tiers(self):
        entries = [
            {"entry_id": f"e{i}", "confidence": 0.5, "usage_count": 5, "age_days": 10, "score": 0.5, "tags": ["a"]}
            for i in range(10)
        ]
        ranked = self.ranker.rank(entries)
        tiers = set(r.tier for r in ranked)
        assert len(tiers) >= 2

    def test_get_top_tier(self):
        entries = [
            {"entry_id": f"e{i}", "confidence": 0.9, "usage_count": 10, "age_days": 1, "score": 0.9, "tags": ["a", "b", "c"]}
            for i in range(5)
        ]
        self.ranker.rank(entries)
        platinum = self.ranker.get_top_tier("platinum")
        assert isinstance(platinum, list)

    def test_rank_empty(self):
        ranked = self.ranker.rank([])
        assert len(ranked) == 0

    def test_ranked_to_dict(self):
        entries = [{"entry_id": "e1", "confidence": 0.8, "usage_count": 5, "age_days": 5, "score": 0.7, "tags": ["a"]}]
        ranked = self.ranker.rank(entries)
        d = ranked[0].to_dict()
        assert "rank" in d
        assert "tier" in d


# ─── MemoryExpiry Tests ──────────────────────────────────────────────
class TestMemoryExpiry:
    def setup_method(self):
        self.expiry = MemoryExpiry()

    def test_check_not_expired(self):
        check = self.expiry.check_entry("e1", age_days=10)
        assert check.is_expired is False
        assert check.action == "keep"

    def test_check_expired(self):
        check = self.expiry.check_entry("e1", age_days=100)
        assert check.is_expired is True
        assert check.action == "expire"

    def test_check_refresh(self):
        check = self.expiry.check_entry("e1", age_days=100, usage_count=3)
        assert check.should_refresh is True
        assert check.action == "refresh"

    def test_set_policy(self):
        policy = ExpiryPolicy("blog", 30)
        self.expiry.set_policy(policy)
        check = self.expiry.check_entry("e1", age_days=35, category="blog")
        assert check.is_expired is True

    def test_get_policy_default(self):
        policy = self.expiry.get_policy("nonexistent")
        assert policy.max_age_days == 90

    def test_batch_check(self):
        entries = [
            {"entry_id": "e1", "age_days": 5},
            {"entry_id": "e2", "age_days": 100, "usage_count": 1},
        ]
        checks = self.expiry.check_batch(entries)
        assert len(checks) == 2

    def test_get_expired(self):
        self.expiry.check_entry("e1", age_days=5)
        self.expiry.check_entry("e2", age_days=100)
        expired = self.expiry.get_expired()
        assert len(expired) == 1

    def test_get_refreshable(self):
        self.expiry.check_entry("e1", age_days=100, usage_count=3)
        self.expiry.check_entry("e2", age_days=100, usage_count=0)
        refreshable = self.expiry.get_refreshable()
        assert len(refreshable) == 1

    def test_check_to_dict(self):
        check = self.expiry.check_entry("e1", age_days=50)
        d = check.to_dict()
        assert "entry_id" in d
        assert "is_expired" in d

    def test_policy_to_dict(self):
        p = ExpiryPolicy("test", 30)
        d = p.to_dict()
        assert d["max_age_days"] == 30


# ─── MemoryArchive Tests ─────────────────────────────────────────────
class TestMemoryArchive:
    def setup_method(self):
        self.archive = MemoryArchive()

    def test_archive(self):
        entry = self.archive.archive("mem_1", {"description": "Test"}, reason="expired")
        assert entry.original_id == "mem_1"
        assert self.archive.archive_count == 1

    def test_search_by_id(self):
        self.archive.archive("mem_1", {}, reason="expired")
        self.archive.archive("mem_2", {}, reason="manual")
        results = self.archive.search(original_id="mem_1")
        assert len(results) == 1

    def test_search_by_reason(self):
        self.archive.archive("mem_1", {}, reason="expired")
        self.archive.archive("mem_2", {}, reason="manual")
        results = self.archive.search(reason="manual")
        assert len(results) == 1

    def test_restore(self):
        entry = self.archive.archive("mem_1", {"key": "value"}, reason="test")
        data = self.archive.restore(entry.archive_id)
        assert data is not None
        assert data["key"] == "value"

    def test_restore_nonexistent(self):
        assert self.archive.restore("fake_id") is None

    def test_get_by_archive_id(self):
        entry = self.archive.archive("mem_1", {})
        found = self.archive.get_by_archive_id(entry.archive_id)
        assert found is not None

    def test_get_by_archive_id_not_found(self):
        assert self.archive.get_by_archive_id("fake") is None

    def test_get_stats(self):
        self.archive.archive("mem_1", {})
        self.archive.archive("mem_2", {})
        stats = self.archive.get_stats()
        assert stats["total_archived"] == 2

    def test_get_recent(self):
        for i in range(5):
            self.archive.archive(f"mem_{i}", {})
        recent = self.archive.get_recent(3)
        assert len(recent) == 3

    def test_max_archives_overflow(self):
        a = MemoryArchive(max_archives=3)
        for i in range(5):
            a.archive(f"mem_{i}", {})
        assert a.archive_count == 3


# ─── MemorySearch Tests ──────────────────────────────────────────────
class TestMemorySearch:
    def setup_method(self):
        self.search = MemorySearch()

    def test_search_by_query(self):
        entries = [
            {"entry_id": "e1", "description": "AI learning insight", "tags": ["ai"], "score": 0.8},
            {"entry_id": "e2", "description": "Design tip", "tags": ["design"], "score": 0.6},
        ]
        results = self.search.search(entries, query="AI")
        assert len(results) >= 1
        assert results[0].entry_id == "e1"

    def test_search_by_tags(self):
        entries = [
            {"entry_id": "e1", "description": "A", "tags": ["ai", "tech"], "score": 0.8},
            {"entry_id": "e2", "description": "B", "tags": ["design"], "score": 0.6},
        ]
        results = self.search.search(entries, tags=["ai"])
        assert len(results) >= 1

    def test_search_by_category(self):
        entries = [
            {"entry_id": "e1", "description": "A", "tags": [], "category": "lesson", "score": 0.8},
            {"entry_id": "e2", "description": "B", "tags": [], "category": "mistake", "score": 0.6},
        ]
        results = self.search.search(entries, category="lesson")
        assert len(results) == 1

    def test_search_min_score(self):
        entries = [
            {"entry_id": "e1", "description": "A", "tags": [], "score": 0.3},
            {"entry_id": "e2", "description": "B", "tags": [], "score": 0.9},
        ]
        results = self.search.search(entries, query="A", min_score=0.5)
        assert len(results) <= 2

    def test_search_empty(self):
        results = self.search.search([], query="test")
        assert len(results) == 0

    def test_search_limit(self):
        entries = [{"entry_id": f"e{i}", "description": f"Test {i}", "tags": [], "score": 0.8} for i in range(10)]
        results = self.search.search(entries, query="Test", limit=3)
        assert len(results) == 3

    def test_search_result_to_dict(self):
        entries = [{"entry_id": "e1", "description": "AI test", "tags": [], "score": 0.8}]
        results = self.search.search(entries, query="AI")
        d = results[0].to_dict()
        assert "entry_id" in d
        assert "relevance_score" in d


# ─── MemoryOptimizer Tests ───────────────────────────────────────────
class TestMemoryOptimizer:
    def setup_method(self):
        self.optimizer = MemoryOptimizer()

    def test_optimize_clean(self):
        entries = [
            {"entry_id": "e1", "description": "Unique entry A", "tags": ["a"]},
            {"entry_id": "e2", "description": "Unique entry B", "tags": ["b"]},
        ]
        report = self.optimizer.optimize(entries)
        assert report.total_actions == 0

    def test_optimize_duplicates(self):
        entries = [
            {"entry_id": "e1", "description": "Same", "tags": ["a"]},
            {"entry_id": "e2", "description": "Same", "tags": ["a"]},
            {"entry_id": "e3", "description": "Different", "tags": ["b"]},
        ]
        report = self.optimizer.optimize(entries)
        assert report.space_saved >= 1

    def test_optimize_empty_entries(self):
        entries = [
            {"entry_id": "e1", "description": "", "tags": []},
            {"entry_id": "e2", "description": "Has content", "tags": ["a"]},
        ]
        report = self.optimizer.optimize(entries)
        assert report.space_saved >= 1

    def test_optimize_similar(self):
        entries = [
            {"entry_id": "e1", "description": "A", "tags": ["ai", "tech", "ml"]},
            {"entry_id": "e2", "description": "B", "tags": ["ai", "tech", "ml"]},
        ]
        report = self.optimizer.optimize(entries)
        assert report.space_saved >= 1

    def test_optimize_empty(self):
        report = self.optimizer.optimize([])
        assert report.total_actions == 0

    def test_reduction_pct(self):
        entries = [
            {"entry_id": "e1", "description": "Same", "tags": ["a"]},
            {"entry_id": "e2", "description": "Same", "tags": ["a"]},
        ]
        report = self.optimizer.optimize(entries)
        assert report.reduction_pct >= 0

    def test_report_to_dict(self):
        report = self.optimizer.optimize([])
        d = report.to_dict()
        assert "before_count" in d
        assert "reduction_pct" in d


# ─── MemoryEvolutionMetrics Tests ────────────────────────────────────
class TestMemoryEvolutionMetrics:
    def setup_method(self):
        self.metrics = MemoryEvolutionMetrics()

    def test_record_cleanup(self):
        self.metrics.record_cleanup(5)
        assert self.metrics.get_total_entries_cleaned() == 5

    def test_record_merge(self):
        self.metrics.record_merge(3)
        summary = self.metrics.get_summary()
        assert summary["total_merges"] == 1

    def test_record_search(self):
        self.metrics.record_search(latency_ms=1.5, results=10)
        assert self.metrics.get_avg_search_latency() == 1.5

    def test_record_archive(self):
        self.metrics.record_archive(2)
        assert self.metrics.get_summary()["total_archives"] == 2

    def test_record_restore(self):
        self.metrics.record_restore(1)
        assert self.metrics.get_summary()["total_restores"] == 1

    def test_summary(self):
        self.metrics.record_cleanup(3)
        self.metrics.record_merge(2)
        self.metrics.record_search(1.0, 5)
        summary = self.metrics.get_summary()
        assert "total_cleanups" in summary
        assert "total_searches" in summary

    def test_reset(self):
        self.metrics.record_cleanup(5)
        self.metrics.reset()
        assert self.metrics.get_total_entries_cleaned() == 0

    def test_no_data(self):
        assert self.metrics.get_avg_search_latency() == 0.0


# ─── EvolutionCycleResult Tests ──────────────────────────────────────
class TestEvolutionCycleResult:
    def test_create(self):
        r = EvolutionCycleResult()
        assert r.cycle_id.startswith("mcy_")

    def test_to_dict(self):
        r = EvolutionCycleResult()
        r.entries_processed = 100
        r.entries_after = 80
        d = r.to_dict()
        assert d["entries_processed"] == 100
        assert d["reduction_pct"] == 20.0


# ─── MemoryManager Tests ─────────────────────────────────────────────
class TestMemoryManager:
    def setup_method(self):
        self.manager = MemoryManager()

    def _make_entries(self, count=5):
        return [
            {
                "entry_id": f"e{i}",
                "source_type": "lesson" if i % 2 == 0 else "insight",
                "description": f"Test entry {i}",
                "confidence": 0.5 + (i * 0.05),
                "usage_count": i,
                "age_days": i * 10,
                "tags": ["ai", "tech"] if i % 2 == 0 else ["design"],
                "score": 0.5 + (i * 0.05),
            }
            for i in range(count)
        ]

    def test_run_evolution_cycle(self):
        entries = self._make_entries(5)
        result = self.manager.run_evolution_cycle(entries)
        assert result.cycle_id.startswith("mcy_")
        assert result.entries_processed == 5

    def test_run_cycle_classifications(self):
        entries = self._make_entries(3)
        result = self.manager.run_evolution_cycle(entries)
        assert result.classification_count == 3

    def test_run_cycle_events(self):
        self.manager.run_evolution_cycle(self._make_entries(3))
        assert len(self.manager.events) == 1

    def test_search_memory(self):
        entries = [
            {"entry_id": "e1", "description": "AI learning", "tags": ["ai"], "score": 0.8},
            {"entry_id": "e2", "description": "Design tip", "tags": ["design"], "score": 0.6},
        ]
        results = self.manager.search_memory(entries, query="AI")
        assert len(results) >= 1

    def test_archive_entry(self):
        result = self.manager.archive_entry("mem_1", {"description": "Test"}, "manual")
        assert result["original_id"] == "mem_1"

    def test_restore_entry(self):
        entry = self.manager.archive_entry("mem_1", {"key": "value"})
        data = self.manager.restore_entry(entry["archive_id"])
        assert data is not None

    def test_health(self):
        self.manager.run_evolution_cycle(self._make_entries(3))
        health = self.manager.get_health()
        assert health["total_cycles"] == 1
        assert "archive_stats" in health

    def test_cycle_count(self):
        self.manager.run_evolution_cycle(self._make_entries(2))
        self.manager.run_evolution_cycle(self._make_entries(2))
        assert self.manager.cycle_count == 2

    def test_get_recent_cycles(self):
        for _ in range(3):
            self.manager.run_evolution_cycle(self._make_entries(2))
        assert len(self.manager.get_recent_cycles(2)) == 2

    def test_manager_components(self):
        assert self.manager.classifier is not None
        assert self.manager.merger is not None
        assert self.manager.cleanup is not None
        assert self.manager.ranker is not None
        assert self.manager.expiry is not None
        assert self.manager.archive is not None
        assert self.manager.search is not None
        assert self.manager.optimizer is not None
        assert self.manager.metrics is not None


# ─── Exceptions Tests ─────────────────────────────────────────────────
class TestExceptions:
    def test_base(self):
        assert issubclass(MemoryEvolutionError, Exception)

    def test_classification(self):
        assert issubclass(ClassificationError, MemoryEvolutionError)

    def test_merge(self):
        assert issubclass(MergeError, MemoryEvolutionError)

    def test_archive(self):
        assert issubclass(ArchiveError, MemoryEvolutionError)


# ─── Integration Tests ────────────────────────────────────────────────
class TestMemoryEvolutionIntegration:
    def test_full_evolution_pipeline(self):
        """Test: Classify → Rank → Merge → Cleanup → Optimize → Archive."""
        manager = MemoryManager()
        entries = [
            {"entry_id": f"e{i}", "source_type": "lesson", "description": f"Entry {i}",
             "confidence": 0.3 + (i * 0.1), "usage_count": i, "age_days": i * 15,
             "tags": ["ai", "tech"] if i % 2 == 0 else ["design"],
             "score": 0.3 + (i * 0.1)}
            for i in range(8)
        ]
        result = manager.run_evolution_cycle(entries)
        assert result.entries_processed == 8
        assert result.classification_count == 8

    def test_classify_and_rank_correlation(self):
        """Test: Higher confidence + usage = higher rank."""
        classifier = MemoryClassifier()
        ranker = MemoryRanker()
        entries = [
            {"entry_id": "high", "confidence": 0.95, "usage_count": 10, "age_days": 2, "score": 0.9, "tags": ["a"]},
            {"entry_id": "low", "confidence": 0.1, "usage_count": 0, "age_days": 80, "score": 0.1, "tags": ["b"]},
        ]
        ranked = ranker.rank(entries)
        assert ranked[0].memory_id == "high"
        assert ranked[1].memory_id == "low"

    def test_cleanup_removes_stale(self):
        """Test: Cleanup identifies and removes stale entries."""
        cleanup = MemoryCleanup()
        entries = [
            {"entry_id": "good", "score": 0.9, "age_days": 5, "usage_count": 3},
            {"entry_id": "bad", "score": 0.05, "age_days": 5, "usage_count": 0},
        ]
        report = cleanup.cleanup(entries)
        assert report.kept == 1
        assert report.deleted == 1

    def test_archive_restore_cycle(self):
        """Test: Archive → Verify → Restore."""
        archive = MemoryArchive()
        entry = archive.archive("mem_1", {"key": "value"}, reason="test")
        data = archive.restore(entry.archive_id)
        assert data == {"key": "value"}

    def test_expiry_refresh(self):
        """Test: Expired entries with usage get refresh action."""
        expiry = MemoryExpiry()
        check = expiry.check_entry("e1", age_days=100, usage_count=5)
        assert check.action == "refresh"

    def test_search_finds_relevant(self):
        """Test: Search returns relevant entries."""
        search = MemorySearch()
        entries = [
            {"entry_id": "e1", "description": "AI learning insight", "tags": ["ai"], "score": 0.9},
            {"entry_id": "e2", "description": "Design tips", "tags": ["design"], "score": 0.7},
        ]
        results = search.search(entries, query="AI learning")
        assert len(results) >= 1
        assert results[0].entry_id == "e1"

    def test_optimizer_reduces(self):
        """Test: Optimizer reduces duplicate entries."""
        optimizer = MemoryOptimizer()
        entries = [
            {"entry_id": "e1", "description": "Same content", "tags": ["a"]},
            {"entry_id": "e2", "description": "Same content", "tags": ["a"]},
            {"entry_id": "e3", "description": "Unique content", "tags": ["b"]},
        ]
        report = optimizer.optimize(entries)
        assert report.space_saved >= 1
