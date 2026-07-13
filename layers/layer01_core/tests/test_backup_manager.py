"""
Tests for Backup Manager Module
Layer 1: Core System — Module 10

Run: python -m pytest layers/layer01_core/tests/test_backup_manager.py -v
"""

import json
import pytest
from layers.layer01_core.modules.backup_manager.backup_manager import BackupManager
from layers.layer01_core.modules.backup_manager.backup_entry import BackupEntry
from layers.layer01_core.modules.backup_manager.exceptions import (
    BackupNotFoundError, BackupIntegrityError,
)


@pytest.fixture
def bm(tmp_path):
    return BackupManager(
        backup_dir=str(tmp_path / "backups"),
        max_backups=10,
        default_retention_days=30,
    )


@pytest.fixture
def sample_files(tmp_path):
    """Create sample files for backup testing."""
    src = tmp_path / "source"
    src.mkdir()
    (src / "data.json").write_text(json.dumps({"key": "value"}))
    (src / "config.yaml").write_text("setting: true")
    (src / "log.txt").write_text("log line 1\nlog line 2\n")
    return src


# ── Test 1: Backup Entry ────────────────────

class TestBackupEntry:
    def test_create_entry(self):
        e = BackupEntry("id1", "database", "file.bak", size_bytes=1024)
        assert e.backup_id == "id1"
        assert e.source == "database"
        assert e.size_bytes == 1024

    def test_to_dict(self):
        e = BackupEntry("id1", "memory", "mem.bak")
        d = e.to_dict()
        assert d["backup_id"] == "id1"
        assert d["source"] == "memory"
        assert "created_at" in d

    def test_from_dict(self):
        d = {"backup_id": "id1", "source": "logs", "filepath": "f.bak",
             "size_bytes": 100, "hash_sha256": "abc", "encrypted": False,
             "compressed": True, "created_at": "2026-01-01T00:00:00",
             "retention_days": 7, "description": "test"}
        e = BackupEntry.from_dict(d)
        assert e.backup_id == "id1"
        assert e.compressed is True
        assert e.retention_days == 7


# ── Test 2: Create Backup ───────────────────

class TestCreateBackup:
    def test_backup_file(self, bm, sample_files):
        entry = bm.backup("database", str(sample_files / "data.json"))
        assert entry is not None
        assert entry.source == "database"
        assert entry.size_bytes > 0
        assert len(entry.hash_sha256) == 64

    def test_backup_directory(self, bm, sample_files):
        entry = bm.backup("memory", str(sample_files))
        assert entry is not None
        assert entry.source == "memory"
        assert entry.size_bytes > 0

    def test_backup_nonexistent(self, bm):
        result = bm.backup("database", "/no/such/file.txt")
        assert result is None

    def test_backup_with_description(self, bm, sample_files):
        entry = bm.backup("database", str(sample_files / "data.json"),
                         description="Before upgrade")
        assert entry.description == "Before upgrade"

    def test_backup_compressed(self, bm, sample_files):
        entry = bm.backup("logs", str(sample_files / "log.txt"), compress=True)
        assert entry.compressed is True

    def test_backup_not_compressed(self, bm, sample_files):
        entry = bm.backup("logs", str(sample_files / "log.txt"), compress=False)
        assert entry.compressed is False

    def test_backup_count_increases(self, bm, sample_files):
        assert bm.count() == 0
        bm.backup("database", str(sample_files / "data.json"))
        assert bm.count() == 1

    def test_backup_json_data(self, bm):
        data = {"name": "test", "values": [1, 2, 3]}
        entry = bm.backup_json("configs", data, filename="test.json")
        assert entry is not None
        assert entry.source == "configs"


# ── Test 3: Restore ─────────────────────────

class TestRestore:
    def test_restore_file(self, bm, sample_files, tmp_path):
        entry = bm.backup("database", str(sample_files / "data.json"))
        target = tmp_path / "restored.json"
        success = bm.restore(entry.backup_id, str(target))
        assert success is True
        assert target.exists()
        data = json.loads(target.read_text())
        assert data["key"] == "value"

    def test_restore_nonexistent_raises(self, bm, tmp_path):
        with pytest.raises(BackupNotFoundError):
            bm.restore("no_such_backup", str(tmp_path / "out.json"))

    def test_restore_integrity_fails(self, bm, sample_files, tmp_path):
        entry = bm.backup("database", str(sample_files / "data.json"),
                         compress=False)
        # Tamper with the backup file
        backup_file = bm._backup_dir / entry.filepath
        backup_file.write_text("TAMPERED")
        with pytest.raises(BackupIntegrityError):
            bm.restore(entry.backup_id, str(tmp_path / "out.json"))


# ── Test 4: Integrity ───────────────────────

class TestIntegrity:
    def test_verify_valid(self, bm, sample_files):
        entry = bm.backup("database", str(sample_files / "data.json"))
        assert bm.verify_integrity(entry.backup_id) is True

    def test_verify_tampered(self, bm, sample_files):
        entry = bm.backup("database", str(sample_files / "data.json"),
                         compress=False)
        backup_file = bm._backup_dir / entry.filepath
        backup_file.write_text("CORRUPTED")
        assert bm.verify_integrity(entry.backup_id) is False

    def test_verify_nonexistent(self, bm):
        assert bm.verify_integrity("nope") is False

    def test_verify_all(self, bm, sample_files):
        bm.backup("database", str(sample_files / "data.json"))
        bm.backup("memory", str(sample_files / "config.yaml"))
        results = bm.verify_all()
        assert len(results) == 2
        assert all(results.values())


# ── Test 5: Rotation ────────────────────────

class TestRotation:
    def test_rotate_expired(self, bm, sample_files):
        entry = bm.backup("database", str(sample_files / "data.json"),
                         retention_days=0)
        removed = bm.rotate()
        assert removed >= 1

    def test_rotate_respects_retention(self, bm, sample_files):
        bm.backup("database", str(sample_files / "data.json"),
                  retention_days=365)
        removed = bm.rotate()
        assert removed == 0

    def test_rotate_max_limit(self, bm, sample_files):
        for i in range(12):
            bm.backup("database", str(sample_files / "data.json"))
        removed = bm.rotate()
        assert removed >= 2
        assert bm.count() <= 10


# ── Test 6: Listing & Queries ───────────────

class TestListing:
    def test_list_all(self, bm, sample_files):
        bm.backup("database", str(sample_files / "data.json"))
        bm.backup("memory", str(sample_files / "config.yaml"))
        backups = bm.list_backups()
        assert len(backups) == 2

    def test_list_by_source(self, bm, sample_files):
        bm.backup("database", str(sample_files / "data.json"))
        bm.backup("memory", str(sample_files / "config.yaml"))
        db_backups = bm.list_backups(source="database")
        assert len(db_backups) == 1

    def test_get_entry(self, bm, sample_files):
        entry = bm.backup("database", str(sample_files / "data.json"))
        found = bm.get_entry(entry.backup_id)
        assert found.source == "database"

    def test_get_entry_not_found(self, bm):
        with pytest.raises(BackupNotFoundError):
            bm.get_entry("nope")

    def test_delete_backup(self, bm, sample_files):
        entry = bm.backup("database", str(sample_files / "data.json"))
        assert bm.count() == 1
        bm.delete_backup(entry.backup_id)
        assert bm.count() == 0

    def test_delete_nonexistent(self, bm):
        with pytest.raises(BackupNotFoundError):
            bm.delete_backup("nope")

    def test_count_by_source(self, bm, sample_files):
        bm.backup("database", str(sample_files / "data.json"))
        bm.backup("memory", str(sample_files / "config.yaml"))
        assert bm.count("database") == 1
        assert bm.count("memory") == 1

    def test_total_size(self, bm, sample_files):
        bm.backup("database", str(sample_files / "data.json"))
        assert bm.total_size() > 0


# ── Test 7: Disaster Recovery ───────────────

class TestDisasterRecovery:
    def test_disaster_recovery(self, bm, sample_files, tmp_path):
        bm.backup("database", str(sample_files / "data.json"))
        bm.backup("memory", str(sample_files / "config.yaml"))
        target = tmp_path / "recovery"
        results = bm.disaster_recovery(str(target))
        assert len(results) == 2
        assert all(results.values())


# ── Test 8: Audit Trail ────────────────────

class TestAudit:
    def test_audit_log_recorded(self, bm, sample_files):
        bm.backup("database", str(sample_files / "data.json"))
        log = bm.get_audit_log()
        assert len(log) >= 1
        assert log[-1]["action"] == "CREATE"

    def test_audit_log_limit(self, bm, sample_files):
        for i in range(10):
            bm.backup("database", str(sample_files / "data.json"))
        log = bm.get_audit_log(limit=5)
        assert len(log) == 5


# ── Test 9: Health Check ────────────────────

class TestHealthCheck:
    def test_health_check_empty(self, bm):
        report = bm.health_check()
        assert report["overall"] == "WARN"
        assert "backups" in report["checks"]

    def test_health_check_with_backups(self, bm, sample_files):
        bm.backup("database", str(sample_files / "data.json"))
        report = bm.health_check()
        assert report["overall"] == "PASS"

    def test_health_check_expired_warns(self, bm, sample_files):
        bm.backup("database", str(sample_files / "data.json"),
                  retention_days=0)
        report = bm.health_check()
        assert report["overall"] == "WARN"
