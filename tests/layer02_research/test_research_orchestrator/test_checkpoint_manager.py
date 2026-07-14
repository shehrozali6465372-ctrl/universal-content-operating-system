"""Tests for CheckpointManager."""

from layers.layer02_research.modules.research_orchestrator.checkpoint_manager import CheckpointManager


class TestCheckpointManager:
    def setup_method(self):
        self.cm = CheckpointManager()

    def test_save_checkpoint(self):
        cp = self.cm.save_checkpoint("exec_1", "trend_discovery", {"step": 1})
        assert cp["module"] == "trend_discovery"
        assert "integrity_hash" in cp

    def test_get_last_checkpoint(self):
        self.cm.save_checkpoint("exec_1", "m1", {"step": 1})
        self.cm.save_checkpoint("exec_1", "m2", {"step": 2})
        last = self.cm.get_last_checkpoint("exec_1")
        assert last["module"] == "m2"

    def test_get_last_checkpoint_empty(self):
        assert self.cm.get_last_checkpoint("nonexistent") is None

    def test_get_checkpoint_at_module(self):
        self.cm.save_checkpoint("exec_1", "m1", {})
        self.cm.save_checkpoint("exec_1", "m2", {})
        self.cm.save_checkpoint("exec_1", "m3", {})
        cp = self.cm.get_checkpoint_at_module("exec_1", "m2")
        assert cp["module"] == "m2"

    def test_get_all_checkpoints(self):
        self.cm.save_checkpoint("exec_1", "m1", {})
        self.cm.save_checkpoint("exec_1", "m2", {})
        all_cps = self.cm.get_all_checkpoints("exec_1")
        assert len(all_cps) == 2

    def test_restore_from_checkpoint(self):
        self.cm.save_checkpoint("exec_1", "m1", {"data": "test"}, ["m1"], 0.8)
        restored = self.cm.restore_from_checkpoint("exec_1")
        assert restored is not None
        assert restored["module"] == "m1"
        assert restored["confidence"] == 0.8

    def test_restore_empty(self):
        assert self.cm.restore_from_checkpoint("nonexistent") is None

    def test_verify_integrity(self):
        cp = self.cm.save_checkpoint("exec_1", "m1", {"data": 42})
        assert self.cm.verify_integrity(cp) is True

    def test_verify_integrity_tampered(self):
        cp = self.cm.save_checkpoint("exec_1", "m1", {"data": 42})
        cp["state"] = {"data": 999}  # tamper
        assert self.cm.verify_integrity(cp) is False

    def test_clear_checkpoints(self):
        self.cm.save_checkpoint("exec_1", "m1", {})
        self.cm.clear_checkpoints("exec_1")
        assert self.cm.get_last_checkpoint("exec_1") is None

    def test_get_module_to_resume_from(self):
        self.cm.save_checkpoint("exec_1", "m1", {})
        self.cm.save_checkpoint("exec_1", "m2", {})
        module = self.cm.get_module_to_resume_from("exec_1")
        assert module == "m2"

    def test_max_checkpoints(self):
        cm = CheckpointManager(max_checkpoints=3)
        for i in range(5):
            cm.save_checkpoint("exec_1", f"m{i}", {})
        all_cps = cm.get_all_checkpoints("exec_1")
        assert len(all_cps) == 3

    def test_integrity_hash_consistent(self):
        cp1 = self.cm.save_checkpoint("exec_1", "m1", {"key": "val"})
        cp2 = self.cm.save_checkpoint("exec_1", "m1", {"key": "val"})
        # Same data should produce different hashes (different timestamps in checkpoint)
        # but both should be valid
        assert self.cm.verify_integrity(cp1)
        assert self.cm.verify_integrity(cp2)
