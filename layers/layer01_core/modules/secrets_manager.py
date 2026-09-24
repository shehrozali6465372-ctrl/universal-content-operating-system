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
from threading import RLock

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    FERNET_AVAILABLE = True
except ImportError:
    FERNET_AVAILABLE = False

from layers.layer01_core.modules.key_store import KeyStore
from layers.layer01_core.modules.audit_logger import AuditLogger
from layers.layer01_core.modules.exceptions import InvalidConfig, SecretAccessError


class SecretsManager:
    """Production-grade encrypted secret storage with audit and health check."""

    def __init__(
        self,
        secrets_path: str = ".secrets",
        audit_log_path: str = "logs/audit.log",
        project_root: Optional[str] = None,
    ):
        self._project_root = (Path(project_root) if project_root else Path.cwd()).resolve()
        secrets_file = (self._project_root / secrets_path).resolve()
        audit_file = (self._project_root / audit_log_path).resolve()
        try:
            secrets_file.relative_to(self._project_root)
            audit_file.relative_to(self._project_root)
        except ValueError as exc:
            raise ValueError("Secrets or audit path escapes project root") from exc
        self._key_store = KeyStore(str(secrets_file))
        self._audit = AuditLogger(str(audit_file))
        self._fernet: Optional["Fernet"] = None
        self._master_key: Optional[str] = None
        self._lock = RLock()

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
        self._legacy_fernet = Fernet(
            base64.urlsafe_b64encode(master_key.encode().ljust(32, b"\0")[:32])
        )
        self._fernet = None

        self._audit.log("SYSTEM", "HEALTH_CHECK", "SUCCESS", "SecretsManager initialized")
        return self

    def _ensure_setup(self) -> None:
        if self._fernet is None:
            raise InvalidConfig("MASTER_KEY", "SecretsManager not initialized. Call setup() first.")

    # ── Encryption ──────────────────────────

    def _derive_v2_fernet(self, salt: bytes) -> "Fernet":
        """Derive a Fernet key from the master key using a per-secret salt."""
        self._ensure_setup()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600_000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self._master_key.encode("utf-8")))
        return Fernet(key)

    def encrypt(self, value: str) -> str:
        """Encrypt using versioned, salted key derivation."""
        self._ensure_setup()
        salt = os.urandom(16)
        encrypted = self._derive_v2_fernet(salt).encrypt(value.encode("utf-8"))
        return "v2:" + base64.urlsafe_b64encode(salt).decode("ascii") + ":" + encrypted.decode("ascii")

    def decrypt(self, encrypted_value: str) -> str:
        """Decrypt v2 values and legacy pre-v2 Fernet values."""
        self._ensure_setup()
        if encrypted_value.startswith("v2:"):
            parts = encrypted_value.split(":", 2)
            if len(parts) != 3:
                raise ValueError("Malformed v2 secret")
            salt = base64.urlsafe_b64decode(parts[1].encode("ascii"))
            return self._derive_v2_fernet(salt).decrypt(parts[2].encode("ascii")).decode("utf-8")
        return self._legacy_fernet.decrypt(encrypted_value.encode("ascii")).decode("utf-8")

    def is_encrypted(self, value: str) -> bool:
        """Check whether a value is decryptable as a managed secret."""
        if not FERNET_AVAILABLE:
            return False
        try:
            self.decrypt(value)
            return True
        except Exception:
            return False

    # ── Store Operations ────────────────────

    def store(self, name: str, value: str) -> None:
        """Store a secret (encrypts if plaintext)."""
        with self._lock:
            self._ensure_setup()
            encrypted = self.encrypt(value)
            self._key_store.add(name, encrypted)
            self._audit.log(name, "CREATED", "SUCCESS")

    def retrieve(self, name: str) -> Optional[str]:
        """Retrieve and decrypt a secret.

        Missing secrets return None; an existing secret that cannot be
        decrypted is a hard failure so callers cannot mistake corruption,
        wrong-key access, or tampering for a legitimate missing secret.
        """
        self._ensure_setup()
        encrypted = self._key_store.get(name)
        if encrypted is None:
            self._audit.log(name, "ACCESSED", "DENIED", "Secret not found")
            return None
        try:
            decrypted = self.decrypt(encrypted)
            self._audit.log(name, "ACCESSED", "SUCCESS")
            return decrypted
        except Exception as exc:
            # Never persist cryptographic exception text: it may expose
            # implementation/provider details. Keep the audit record generic.
            self._audit.log(name, "FAILED_ACCESS", "FAILED", "Decryption failed")
            raise SecretAccessError(name) from exc

    def delete(self, name: str) -> bool:
        """Delete a secret."""
        with self._lock:
            found = self._key_store.remove(name)
            status = "SUCCESS" if found else "FAILED"
            self._audit.log(name, "DELETED", status)
            return found

    def rotate(self, name: str, new_value: str) -> bool:
        """Replace a secret without a delete-then-create gap."""
        with self._lock:
            self._ensure_setup()
            encrypted = self.encrypt(new_value)
            self._key_store.add(name, encrypted)
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

    def health_check(self) -> Dict[str, object]:
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
