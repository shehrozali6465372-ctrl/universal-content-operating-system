"""
Tests for Secrets Manager Module
Layer 1: Core System — Module 2

Run: python -m pytest layers/layer01_core/tests/test_secrets_manager.py -v
"""

import os
import pytest
from layers.layer01_core.modules.secrets_manager import SecretsManager, FERNET_AVAILABLE


@pytest.fixture
def sm(tmp_path):
    """Create a fresh SecretsManager for each test."""
    manager = SecretsManager(
        secrets_path=str(tmp_path / ".secrets"),
        audit_log_path=str(tmp_path / "logs" / "audit.log"),
        project_root=str(tmp_path),
    )
    manager.setup(master_key="test-master-key-for-testing-1234")
    return manager


# ── Test 1: Setup ──────────────────────────

class TestSetup:
    def test_setup_without_key_uses_env(self, tmp_path):
        os.environ["AGENT_MASTER_KEY"] = "env-key-12345678"
        sm = SecretsManager(project_root=str(tmp_path))
        sm.setup()
        assert sm._master_key == "env-key-12345678"
        del os.environ["AGENT_MASTER_KEY"]

    def test_setup_without_key_raises(self, tmp_path):
        os.environ.pop("AGENT_MASTER_KEY", None)
        from layers.layer01_core.modules.exceptions import InvalidConfig
        sm = SecretsManager(project_root=str(tmp_path))
        with pytest.raises(InvalidConfig):
            sm.setup()

    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_setup_initializes_fernet(self, sm):
        assert sm._fernet is not None


# ── Test 2: Encrypt / Decrypt ──────────────

class TestEncryption:
    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_encrypt_decrypt_roundtrip(self, sm):
        original = "sk-my-openai-api-key-12345"
        encrypted = sm.encrypt(original)
        decrypted = sm.decrypt(encrypted)
        assert decrypted == original
        assert encrypted != original

    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_is_encrypted_detects_fernet(self, sm):
        encrypted = sm.encrypt("test-value")
        assert sm.is_encrypted(encrypted) is True

    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_is_encrypted_rejects_plaintext(self, sm):
        assert sm.is_encrypted("just-plain-text") is False


# ── Test 3: Store / Retrieve ───────────────

class TestStoreRetrieve:
    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_store_and_retrieve(self, sm):
        sm.store("MY_API_KEY", "sk-secret-value-123")
        result = sm.retrieve("MY_API_KEY")
        assert result == "sk-secret-value-123"

    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_retrieve_nonexistent_returns_none(self, sm):
        result = sm.retrieve("DOES_NOT_EXIST")
        assert result is None

    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_exists(self, sm):
        sm.store("KEY1", "val1")
        assert sm.exists("KEY1") is True
        assert sm.exists("KEY2") is False

    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_names(self, sm):
        sm.store("KEY_A", "val_a")
        sm.store("KEY_B", "val_b")
        names = sm.names()
        assert "KEY_A" in names
        assert "KEY_B" in names

    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_count(self, sm):
        sm.store("A", "1")
        sm.store("B", "2")
        assert sm.count() == 2

    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_value_not_stored_in_plaintext(self, sm):
        sm.store("SECRET_KEY", "super-secret-value-xyz")
        raw_content = sm._key_store.path.read_text()
        assert "super-secret-value-xyz" not in raw_content


# ── Test 4: Delete ─────────────────────────

class TestDelete:
    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_delete_existing(self, sm):
        sm.store("TO_DELETE", "value")
        assert sm.delete("TO_DELETE") is True
        assert sm.exists("TO_DELETE") is False

    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_delete_nonexistent(self, sm):
        assert sm.delete("NOPE") is False


# ── Test 5: Rotate ─────────────────────────

class TestRotate:
    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_rotate_old_value_gone(self, sm):
        sm.store("API_KEY", "old-value")
        sm.rotate("API_KEY", "new-value")
        assert sm.retrieve("API_KEY") == "new-value"
        assert sm.count() == 1


# ── Test 6: Bulk Operations ────────────────

class TestBulk:
    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_store_multiple(self, sm):
        sm.store_multiple({"K1": "v1", "K2": "v2", "K3": "v3"})
        assert sm.count() == 3

    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_retrieve_multiple(self, sm):
        sm.store_multiple({"K1": "v1", "K2": "v2"})
        results = sm.retrieve_multiple(["K1", "K2", "MISSING"])
        assert results["K1"] == "v1"
        assert results["K2"] == "v2"
        assert results["MISSING"] is None


# ── Test 7: Audit Log ──────────────────────

class TestAuditLog:
    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_store_creates_audit_entry(self, sm):
        sm.store("AUDIT_KEY", "value")
        logs = sm.get_audit_logs()
        assert len(logs) >= 1
        assert logs[-1]["secret_name"] == "AUDIT_KEY"
        assert logs[-1]["action"] == "CREATED"
        assert logs[-1]["status"] == "SUCCESS"

    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_delete_creates_audit_entry(self, sm):
        sm.store("DEL_KEY", "val")
        sm.delete("DEL_KEY")
        logs = sm.get_audit_for_secret("DEL_KEY")
        actions = [l["action"] for l in logs]
        assert "CREATED" in actions
        assert "DELETED" in actions

    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_failed_access_audited(self, sm):
        sm.retrieve("NO_SUCH_KEY")
        logs = sm.get_audit_for_secret("NO_SUCH_KEY")
        assert any(l["action"] == "ACCESSED" and l["status"] == "DENIED" for l in logs)

    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_audit_never_logs_values(self, sm):
        sm.store("AUDIT_SECRET", "my-super-secret-value-abc")
        logs = sm.get_audit_logs()
        raw_log_text = str(logs)
        assert "my-super-secret-value-abc" not in raw_log_text


# ── Test 8: Health Check ───────────────────

class TestHealthCheck:
    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_health_check_pass(self, sm):
        sm.store("TEST_KEY", "test-value")
        report = sm.health_check()
        assert report["overall"] == "PASS"
        assert report["checks"]["master_key"]["status"] == "PASS"
        assert report["checks"]["encryption"]["status"] == "PASS"

    @pytest.mark.skipif(not FERNET_AVAILABLE, reason="cryptography not installed")
    def test_health_check_without_key_warns(self, tmp_path):
        sm = SecretsManager(project_root=str(tmp_path))
        # No setup() called → no master key
        report = sm.health_check()
        assert report["checks"]["master_key"]["status"] == "FAIL"
        assert report["overall"] == "FAIL"
