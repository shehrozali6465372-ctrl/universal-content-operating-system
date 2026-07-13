"""
Secrets Manager Module
Layer 1: Core System — Module 2

Production-grade secret management with:
- Fernet encryption (via cryptography library)
- Audit logging (NEVER logs values)
- Health check system
- Key rotation support

Usage:
    from layers.layer01_core.modules.secrets_manager import SecretsManager

    sm = SecretsManager()
    sm.setup(master_key="my-master-key")

    # Store
    sm.store("OPENAI_API_KEY", "sk-actual-key-here")

    # Retrieve
    api_key = sm.retrieve("OPENAI_API_KEY")

    # Rotate
    sm.rotate("OPENAI_API_KEY", "sk-new-key-here")

    # Health check
    report = sm.health_check()
"""

import os
import base64
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime, timezone

try:
    from cryptography.fernet import Fernet
    FERNET_AVAILABLE = True
except ImportError:
    FERNET_AVAILABLE = False

from layers.layer01_core.modules.key_store import KeyStore
from layers.layer01_core.modules.audit_logger import AuditLogger
from layers.layer01_core.modules.exceptions import InvalidConfig


class SecretsManager:
    """Production-grade encrypted secret storage with audit and health check."""

    def __init__(
        self,
        secrets_path: str = ".secrets",
        audit_log_path: str = "logs/audit.log",
        project_root: Optional[str] = None,
    ):
        self._project_root = Path(project_root) if project_root else Path.cwd()
        self._key_store = KeyStore(str(self._project_root / secrets_path))
        self._audit = AuditLogger(str(self._project_root / audit_log_path))
        self._fernet: Optional["Fernet"] = None
        self._master_key: Optional[str] = None

    # ── Setup ───────────────────────────────

    def setup(self, master_key: Optional[str] = None) -> "SecretsManager":
        """Initialize encryption with master key."""
        if not FERNET_AVAILABLE:
            raise ImportError(
                "cryptography library required. Install: pip install cryptography"
            )

        if master_key is None:
            master_key = os.environ.get("AGENT_MASTER_KEY", "")

        if not master_key:
            raise InvalidConfig(
                "MASTER_KEY",
                "Master key not provided. Set AGENT_MASTER_KEY env var or pass master_key param."
            )

        self._master_key = master_key
        derived_key = base64.urlsafe_b64encode(master_key.encode().ljust(32, b"\0")[:32])
        self._fernet = Fernet(derived_key)

        self._audit.log("SYSTEM", "HEALTH_CHECK", "SUCCESS", "SecretsManager initialized")
        return self

    def _ensure_setup(self) -> None:
        if self._fernet is None:
            raise InvalidConfig("MASTER_KEY", "SecretsManager not initialized. Call setup() first.")

    # ── Encryption ──────────────────────────

    def encrypt(self, value: str) -> str:
        """Encrypt a plaintext value."""
        self._ensure_setup()
        encrypted = self._fernet.encrypt(value.encode())
        return encrypted.decode()

    def decrypt(self, encrypted_value: str) -> str:
        """Decrypt an encrypted value."""
        self._ensure_setup()
        decrypted = self._fernet.decrypt(encrypted_value.encode())
        return decrypted.decode()

    def is_encrypted(self, value: str) -> bool:
        """Check if a value is already encrypted (Fernet format)."""
        if not FERNET_AVAILABLE:
            return False
        try:
            self._ensure_setup()
            self._fernet.decrypt(value.encode())
            return True
        except Exception:
            return False

    # ── Store Operations ────────────────────

    def store(self, name: str, value: str) -> None:
        """Store a secret (encrypts if plaintext)."""
        self._ensure_setup()
        if self.is_encrypted(value):
            encrypted = value
        else:
            encrypted = self.encrypt(value)
        self._key_store.add(name, encrypted)
        self._audit.log(name, "CREATED", "SUCCESS")

    def retrieve(self, name: str) -> Optional[str]:
        """Retrieve and decrypt a secret."""
        self._ensure_setup()
        encrypted = self._key_store.get(name)
        if encrypted is None:
            self._audit.log(name, "ACCESSED", "DENIED", "Secret not found")
            return None
        try:
            decrypted = self.decrypt(encrypted)
            self._audit.log(name, "ACCESSED", "SUCCESS")
            return decrypted
        except Exception as e:
            self._audit.log(name, "FAILED_ACCESS", "FAILED", str(e))
            return None

    def delete(self, name: str) -> bool:
        """Delete a secret."""
        found = self._key_store.remove(name)
        status = "SUCCESS" if found else "FAILED"
        self._audit.log(name, "DELETED", status)
        return found

    def rotate(self, name: str, new_value: str) -> bool:
        """Delete old secret and store new one."""
        self.delete(name)
        self.store(name, new_value)
        self._audit.log(name, "ROTATED", "SUCCESS")
        return True

    def exists(self, name: str) -> bool:
        """Check if a secret exists."""
        return self._key_store.has(name)

    def names(self) -> List[str]:
        """List all secret names (no values)."""
        return self._key_store.names()

    def count(self) -> int:
        """Count total secrets."""
        return self._key_store.count()

    # ── Bulk Operations ─────────────────────

    def store_multiple(self, secrets: Dict[str, str]) -> None:
        """Store multiple secrets at once."""
        for name, value in secrets.items():
            self.store(name, value)

    def retrieve_multiple(self, names: List[str]) -> Dict[str, Optional[str]]:
        """Retrieve multiple secrets."""
        return {name: self.retrieve(name) for name in names}

    # ── Health Check ────────────────────────

    def health_check(self) -> Dict[str, any]:
        """
        Run full health check:
        1. Master key present?
        2. .secrets file exists?
        3. Encryption working?
        4. Permissions correct?
        """
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
            "overall": "PASS",
        }

        # Check 1: Master Key
        report["checks"]["master_key"] = {
            "status": "PASS" if self._master_key else "FAIL",
            "message": "Master key loaded" if self._master_key else "Master key missing",
        }

        # Check 2: .secrets file
        report["checks"]["secrets_file"] = {
            "status": "PASS" if self._key_store.exists else "WARN",
            "message": f"File exists ({self._key_store.count()} secrets)" if self._key_store.exists
                       else "No .secrets file (will be created on first store)",
        }

        # Check 3: Encryption working
        try:
            self._ensure_setup()
            test_value = "health-check-test"
            encrypted = self.encrypt(test_value)
            decrypted = self.decrypt(encrypted)
            enc_ok = decrypted == test_value
            report["checks"]["encryption"] = {
                "status": "PASS" if enc_ok else "FAIL",
                "message": "Fernet encrypt/decrypt working" if enc_ok else "Encryption broken",
            }
        except Exception as e:
            report["checks"]["encryption"] = {"status": "FAIL", "message": str(e)}

        # Check 4: File permissions
        if self._key_store.exists:
            try:
                mode = oct(self._key_store.path.stat().st_mode)[-3:]
                perm_ok = mode == "600"
                report["checks"]["permissions"] = {
                    "status": "PASS" if perm_ok else "WARN",
                    "message": f"File permissions: {mode}" + (" (correct)" if perm_ok else " (recommended: 600)"),
                }
            except Exception:
                report["checks"]["permissions"] = {"status": "WARN", "message": "Could not check permissions"}
        else:
            report["checks"]["permissions"] = {"status": "SKIP", "message": "No file to check"}

        # Overall
        statuses = [c["status"] for c in report["checks"].values()]
        if "FAIL" in statuses:
            report["overall"] = "FAIL"
        elif "WARN" in statuses:
            report["overall"] = "WARN"

        self._audit.log("SYSTEM", "HEALTH_CHECK", report["overall"])
        return report

    # ── Audit ───────────────────────────────

    def get_audit_logs(self, limit: int = 50) -> list:
        """Get recent audit log entries."""
        return self._audit.get_logs(limit)

    def get_audit_for_secret(self, name: str) -> list:
        """Get audit logs for a specific secret."""
        return self._audit.get_logs_for_secret(name)

    # ── Reset ───────────────────────────────

    def reset(self) -> None:
        """Clear all secrets and audit logs."""
        self._key_store.clear()
        self._audit.clear()
