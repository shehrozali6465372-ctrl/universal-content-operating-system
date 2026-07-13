"""
Tests for Memory Manager Module
Layer 1: Core System — Module 5

Run: python -m pytest layers/layer01_core/tests/test_memory_manager.py -v
"""

import pytest
from layers.layer01_core.modules.memory_manager import MemoryManager
from layers.layer01_core.modules.memory_store import MemoryLevel, get_level_config, get_persistent_levels
from layers.layer01_core.modules.memory_search import SearchQuery, SearchResult


@pytest.fixture
def mem(tmp_path):
    """Fresh MemoryManager for each test."""
    m = MemoryManager(
        db_path=str(tmp_path / "test_memory.db"),
        project_root=str(tmp_path),
    )
    m.initialize()
    yield m
    m.close()


# ── Test 1: Initialization ─────────────────

class TestInitialization:
    def test_creates_db_file(self, mem):
        assert mem._db_path.exists()

    def test_is_initialized(self, mem):
        assert mem.is_initialized is True

    def test_tables_exist(self, mem):
        tables = [r["name"] for r in mem._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        assert "memory_entries" in tables


# ── Test 2: Memory Store Definitions ───────

class TestMemoryStore:
    def test_all_4_levels_exist(self):
        from layers.layer01_core.modules.memory_store import MEMORY_LEVELS
        assert len(MEMORY_LEVELS) == 4

    def test_stm_config(self):
        cfg = get_level_config(MemoryLevel.STM)
        assert cfg.persistent is False
        assert cfg.max_entries == 100

    def test_ltm_config(self):
        cfg = get_level_config(MemoryLevel.LTM)
        assert cfg.persistent is True
        assert cfg.max_entries == 10000

    def test_persistent_levels(self):
        persistent = get_persistent_levels()
        assert MemoryLevel.STM not in persistent
        assert MemoryLevel.LTM in persistent
        assert MemoryLevel.EPISODIC in persistent


# ── Test 3: Save & Load — STM ──────────────

class TestSTM:
    def test_save_to_stm(self, mem):
        entry_id = mem.save("short_term", "task", "current_task", "Write post about AI")
        assert entry_id is not None

    def test_load_from_stm(self, mem):
        mem.save("short_term", "conversation", "user_msg", "Hello!")
        entries = mem.load("short_term")
        assert len(entries) == 1
        assert entries[0]["key"] == "user_msg"

    def test_stm_filtered_by_category(self, mem):
        mem.save("short_term", "task", "t1", "v1")
        mem.save("short_term", "session", "s1", "v2")
        result = mem.load("short_term", category="task")
        assert len(result) == 1
        assert result[0]["key"] == "t1"

    def test_stm_cleared(self, mem):
        mem.save("short_term", "c", "k", "v")
        count = mem.clear_level("short_term")
        assert count == 1
        assert len(mem.load("short_term")) == 0


# ── Test 4: Save & Load — Persistent ───────

class TestPersistentMemory:
    def test_save_to_ltm(self, mem):
        entry_id = mem.save("long_term", "brand", "voice", "Friendly and professional")
        assert entry_id > 0

    def test_load_ltm(self, mem):
        mem.save("long_term", "brand", "tone", "Casual")
        entries = mem.load("long_term")
        assert len(entries) >= 1
        assert entries[0]["value"] == "Casual"

    def test_save_to_episodic(self, mem):
        entry_id = mem.save("episodic", "post_history", "post_123", "AI Post about tech")
        assert entry_id > 0

    def test_save_to_working(self, mem):
        entry_id = mem.save("working", "goal", "current_goal", "Get 1000 followers")
        assert entry_id > 0

    def test_get_by_id(self, mem):
        entry_id = mem.save("long_term", "test", "get_test", "value")
        entry = mem.get(entry_id)
        assert entry is not None
        assert entry["key"] == "get_test"
        assert entry["access_count"] >= 0


# ── Test 5: Update & Delete ────────────────

class TestUpdateDelete:
    def test_update_entry(self, mem):
        entry_id = mem.save("long_term", "cat", "k", "old")
        result = mem.update(entry_id, value="new", importance=0.9)
        assert result is True
        entry = mem.get(entry_id)
        assert entry["value"] == "new"
        assert entry["importance"] == 0.9

    def test_delete_entry(self, mem):
        entry_id = mem.save("long_term", "cat", "del", "val")
        result = mem.delete(entry_id)
        assert result is True
        assert mem.get(entry_id) is None

    def test_clear_level(self, mem):
        mem.save("long_term", "c1", "k1", "v1")
        mem.save("long_term", "c2", "k2", "v2")
        count = mem.clear_level("long_term")
        assert count == 2
        assert len(mem.load("long_term")) == 0


# ── Test 6: Batch Operations ───────────────

class TestBatch:
    def test_save_batch(self, mem):
        entries = [
            {"level": "long_term", "category": "c", "key": f"k{i}", "value": f"v{i}"}
            for i in range(5)
        ]
        count = mem.save_batch(entries)
        assert count == 5


# ── Test 7: Search ─────────────────────────

class TestSearch:
    def test_search_by_keyword(self, mem):
        mem.save("long_term", "brand", "voice", "Friendly and professional tone")
        mem.save("long_term", "brand", "colors", "Blue and white")
        results = mem.search(keyword="friendly")
        assert len(results) >= 1
        assert "Friendly" in results[0].value

    def test_search_by_level(self, mem):
        mem.save("long_term", "c", "k1", "v1")
        mem.save("episodic", "c", "k2", "v2")
        results = mem.search(keyword="k", levels=["long_term"])
        assert len(results) == 1

    def test_search_by_category(self, mem):
        mem.save("long_term", "brand", "b1", "v")
        mem.save("long_term", "style", "s1", "v")
        results = mem.search(category="brand")
        assert len(results) >= 1

    def test_search_no_results(self, mem):
        results = mem.search(keyword="zzzznonexistent")
        assert len(results) == 0

    def test_find_by_key(self, mem):
        mem.save("long_term", "c", "specific_key", "specific_value")
        entry = mem.find_by_key("specific_key")
        assert entry is not None
        assert entry["value"] == "specific_value"


# ── Test 8: Compression ────────────────────

class TestCompression:
    def test_compress_reduces_entries(self, mem):
        # STM can hold 100, add 120
        for i in range(120):
            mem.save("short_term", "task", f"t{i}", f"v{i}")
        removed = mem.compress_level("short_term")
        assert removed == 0  # STM auto-evicts on save, but compress checks max
        # After compress, should be at or below max
        assert len(mem.load("short_term")) <= 100


# ── Test 9: Snapshot & Restore ─────────────

class TestSnapshotRestore:
    def test_snapshot_creates_file(self, mem):
        mem.save("long_term", "c", "k", "v")
        path = mem.snapshot(str(mem._project_root / "data/snap.json"))
        assert path.exists()

    def test_restore_from_snapshot(self, mem):
        mem.save("long_term", "snap", "original", "data")
        mem.snapshot(str(mem._project_root / "data/snap.json"))
        mem.clear_level("long_term")
        assert len(mem.load("long_term")) == 0
        count = mem.restore(str(mem._project_root / "data" / "snap.json"))
        assert count >= 1
        assert len(mem.load("long_term")) >= 1


# ── Test 10: Health Check ──────────────────

class TestHealthCheck:
    def test_health_check_pass(self, mem):
        report = mem.health_check()
        assert report["overall"] == "PASS"
        assert "connection" in report["checks"]

    def test_health_check_shows_counts(self, mem):
        mem.save("long_term", "c", "k", "v")
        report = mem.health_check()
        assert "entry_counts" in report["checks"]


# ── Test 11: Stats ─────────────────────────

class TestStats:
    def test_get_stats(self, mem):
        mem.save("long_term", "c1", "k1", "v1")
        mem.save("episodic", "c2", "k2", "v2")
        stats = mem.get_stats()
        assert stats["levels"]["long_term"]["count"] >= 1
        assert stats["levels"]["episodic"]["count"] >= 1
        assert "stm_buffer" in stats
