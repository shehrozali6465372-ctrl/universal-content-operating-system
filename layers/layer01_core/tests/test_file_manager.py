"""
Tests for File Manager Module
Layer 1: Core System — Module 8

Run: python -m pytest layers/layer01_core/tests/test_file_manager.py -v
"""

import json
import pytest
from layers.layer01_core.modules.file_manager.file_manager import FileManager
from layers.layer01_core.modules.file_manager.hash_utils import calculate_hash, calculate_string_hash, save_hash, verify_hash
from layers.layer01_core.modules.file_manager.file_cache import FileCache


@pytest.fixture
def fm(tmp_path):
    return FileManager(base_path=str(tmp_path), cache_size=50)


# ── Test 1: Safe Read ──────────────────────

class TestSafeRead:
    def test_read_existing(self, fm):
        (fm._base / "test.txt").write_text("hello")
        assert fm.read("test.txt") == "hello"

    def test_read_nonexistent(self, fm):
        assert fm.read("nope.txt") is None

    def test_read_bytes(self, fm):
        (fm._base / "data.bin").write_bytes(b"\x00\x01\x02")
        assert fm.read_bytes("data.bin") == b"\x00\x01\x02"

    def test_read_uses_cache(self, fm):
        (fm._base / "cached.txt").write_text("cached")
        fm.read("cached.txt")
        assert fm._cache.has(str(fm._base / "cached.txt"))


# ── Test 2: Atomic Write ───────────────────

class TestAtomicWrite:
    def test_write_creates_file(self, fm):
        fm.write("output.txt", "content")
        assert (fm._base / "output.txt").read_text() == "content"

    def test_write_creates_dirs(self, fm):
        fm.write("sub/dir/file.txt", "nested")
        assert (fm._base / "sub/dir/file.txt").exists()

    def test_write_with_backup(self, fm):
        fm.write("old.txt", "version1")
        fm.write("old.txt", "version2")
        assert (fm._base / "old.txt").read_text() == "version2"
        backup_dir = fm._base / "backups"
        backups = list(backup_dir.glob("old.txt.*.bak"))
        assert len(backups) >= 1

    def test_write_with_verify(self, fm):
        fm.write("verified.txt", "data", verify=True)
        assert (fm._base / "verified.txt.sha256").exists()

    def test_append(self, fm):
        fm.write("log.txt", "line1\n")
        fm.append("log.txt", "line2\n")
        content = fm.read("log.txt", use_cache=False)
        assert "line1" in content
        assert "line2" in content


# ── Test 3: File Operations ────────────────

class TestFileOps:
    def test_copy(self, fm):
        fm.write("src.txt", "copy me")
        fm.copy("src.txt", "dst.txt")
        assert fm.read("dst.txt") == "copy me"

    def test_move(self, fm):
        fm.write("before.txt", "moving")
        fm.move("before.txt", "after.txt")
        assert fm.exists("after.txt")
        assert not fm.exists("before.txt")

    def test_delete(self, fm):
        fm.write("del.txt", "bye")
        assert fm.delete("del.txt") is True
        assert fm.exists("del.txt") is False

    def test_delete_nonexistent(self, fm):
        assert fm.delete("ghost.txt") is False

    def test_exists(self, fm):
        fm.write("here.txt", "x")
        assert fm.exists("here.txt") is True
        assert fm.exists("gone.txt") is False

    def test_list_files(self, fm):
        fm.write("a.txt", "a")
        fm.write("b.txt", "b")
        files = fm.list_files(".")
        assert "a.txt" in files
        assert "b.txt" in files


# ── Test 4: Backup & Restore ───────────────

class TestBackupRestore:
    def test_backup(self, fm):
        fm.write("important.txt", "data")
        backup_path = fm.backup("important.txt")
        assert backup_path is not None
        assert fm.exists(backup_path)

    def test_restore(self, fm):
        fm.write("restoreme.txt", "original")
        backup_path = fm.backup("restoreme.txt")
        fm.write("restoreme.txt", "overwritten")
        fm.restore(backup_path, "restoreme.txt")
        assert fm.read("restoreme.txt") == "original"


# ── Test 5: Hash Verification ──────────────

class TestHashVerification:
    def test_calculate_hash(self, fm):
        fm.write("hash_test.txt", "hash me")
        h = fm.calculate_hash("hash_test.txt")
        assert h is not None
        assert len(h) == 64  # SHA-256

    def test_hash_consistency(self, fm):
        fm.write("consistent.txt", "stable")
        h1 = fm.calculate_hash("consistent.txt")
        h2 = fm.calculate_hash("consistent.txt")
        assert h1 == h2

    def test_save_and_verify(self, fm):
        fm.save_and_verify("verified.txt", "safe content")
        match, h = fm.verify_hash("verified.txt")
        assert match is True

    def test_verify_tampered(self, fm):
        fm.save_and_verify("tampered.txt", "original")
        (fm._base / "tampered.txt").write_text("modified")
        match, _ = fm.verify_hash("tampered.txt")
        assert match is False

    def test_string_hash(self):
        h = calculate_string_hash("test")
        assert len(h) == 64


# ── Test 6: Compression ────────────────────

class TestCompression:
    def test_compress(self, fm):
        fm.write("big.txt", "x" * 10000)
        gz_path = fm.compress("big.txt")
        assert gz_path is not None
        assert fm.exists(gz_path)

    def test_decompress(self, fm):
        fm.write("expand.txt", "y" * 5000)
        gz_path = fm.compress("expand.txt")
        out_path = fm.decompress(gz_path)
        assert fm.read(out_path) == "y" * 5000

    def test_compressed_smaller(self, fm):
        fm.write("compressible.txt", "aaaa" * 1000)
        original_size = (fm._base / "compressible.txt").stat().st_size
        gz_path = fm.compress("compressible.txt")
        compressed_size = (fm._base / gz_path).stat().st_size
        assert compressed_size < original_size


# ── Test 7: File Cache ─────────────────────

class TestFileCache:
    def test_cache_basic(self):
        c = FileCache(max_size=3)
        c.set("a", "1")
        assert c.get("a") == "1"

    def test_cache_lru_eviction(self):
        c = FileCache(max_size=2)
        c.set("a", "1")
        c.set("b", "2")
        c.set("c", "3")  # evicts "a"
        assert c.get("a") is None
        assert c.get("b") == "2"
        assert c.get("c") == "3"

    def test_cache_stats(self):
        c = FileCache()
        c.set("x", 1)
        c.get("x")
        c.get("miss")
        stats = c.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert "hit_rate" in stats

    def test_cache_invalidate(self):
        c = FileCache()
        c.set("k", "v")
        c.invalidate("k")
        assert c.get("k") is None


# ── Test 8: Import / Export ────────────────

class TestImportExport:
    def test_export_json(self, fm):
        data = {"key": "value", "list": [1, 2, 3]}
        fm.export_json("data.json", data)
        loaded = fm.import_json("data.json")
        assert loaded == data

    def test_import_json_nonexistent(self, fm):
        assert fm.import_json("nope.json") is None

    def test_export_csv(self, fm):
        fm.export_csv("table.csv", ["name", "age"], [["Ali", 25], ["Sara", 30]])
        rows = fm.import_csv("table.csv")
        assert len(rows) == 2
        assert rows[0]["name"] == "Ali"


# ── Test 9: File Lock ──────────────────────

class TestFileLock:
    def test_acquire_lock(self, fm):
        lock = fm.acquire_lock("shared.txt")
        assert lock is not None

    def test_same_lock_returned(self, fm):
        l1 = fm.acquire_lock("same.txt")
        l2 = fm.acquire_lock("same.txt")
        assert l1 is l2


# ── Test 10: Health Check ──────────────────

class TestHealthCheck:
    def test_health_check(self, fm):
        fm.write("init.txt", "init")
        fm.backup("init.txt")
        report = fm.health_check()
        assert report["overall"] == "PASS"
        assert "base_path" in report["checks"]
        assert "cache" in report["checks"]
        assert "backups" in report["checks"]

    def test_health_check_with_backups(self, fm):
        fm.write("bk.txt", "data")
        fm.backup("bk.txt")
        report = fm.health_check()
        assert "backups" in report["checks"]
