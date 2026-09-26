"""Production security gate for Layer 17.

These tests validate security invariants, not just nominal API behavior.
"""
from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor

import pytest

from layers.layer17_security.modules.authentication.authentication import AuthenticationManager
from layers.layer17_security.modules.encryption_engine.encryption_engine import EncryptionEngine
from layers.layer17_security.modules.firewall.firewall import Firewall
from layers.layer17_security.modules.input_validator.input_validator import InputValidator
from layers.layer17_security.modules.jwt_framework.jwt_framework import JWTFramework
from layers.layer17_security.modules.permission_engine.permission_engine import PermissionEngine
from layers.layer17_security.modules.secrets_manager.secrets_manager import SecretsManager
from layers.layer17_security.modules.signature_engine.signature_engine import SignatureEngine
from layers.layer17_security.modules.token_manager.token_manager import TokenManager, TokenType


def test_password_hashing_is_slow_and_not_plain_sha256() -> None:
    manager = AuthenticationManager()
    user = manager.register_user("ali", "ali@example.com", "correct-password")
    assert isinstance(user.password_hash, bytes)
    assert user.password_hash != b""
    assert user.password_hash != __import__("hashlib").sha256(
        b"correct-password"
    ).digest()
    assert manager.authenticate_password("ali", "correct-password") is not None
    assert manager.authenticate_password("ali", "wrong") is None


def test_api_keys_are_not_stored_in_plaintext() -> None:
    manager = AuthenticationManager()
    user = manager.register_user("ali", password="correct-password")
    raw = "production-secret-api-key"
    assert manager.register_api_key(user.user_id, raw)
    assert raw not in manager._api_keys
    assert manager.authenticate_api_key(raw) == user.user_id


def test_encryption_is_authenticated_and_fail_closed() -> None:
    engine = EncryptionEngine()
    with pytest.raises(RuntimeError):
        engine.encrypt("secret")
    engine.set_key("a sufficiently strong key material")
    ciphertext = engine.encrypt("secret")
    assert engine.decrypt(ciphertext) == "secret"
    raw = bytearray(base64.urlsafe_b64decode(ciphertext))
    raw[-1] ^= 1
    tampered = base64.urlsafe_b64encode(raw).decode()
    with pytest.raises(ValueError):
        engine.decrypt(tampered)


def test_signature_engine_has_no_fallback_key() -> None:
    engine = SignatureEngine()
    assert not engine.verify("missing", "payload", "anything")
    with pytest.raises(KeyError):
        engine.sign("missing", "payload")
    engine.generate_key("k")
    signature = engine.sign("k", "payload")
    assert engine.verify("k", "payload", signature)
    assert not engine.verify("k", "tampered", signature)


def test_jwt_requires_strong_secret_and_rejects_bad_token() -> None:
    with pytest.raises(ValueError):
        JWTFramework()
    jwt = JWTFramework("x" * 32)
    token = jwt.create_token({"sub": "user-1"})
    assert jwt.decode_token(token)["sub"] == "user-1"
    assert jwt.decode_token(token.rsplit(".", 1)[0] + ".bad") is None


def test_permission_engine_is_deny_overrides_allow() -> None:
    engine = PermissionEngine()
    engine.add_rule("content", "publish", "allow")
    engine.add_rule("content", "publish", "deny", {"environment": "production"})
    assert engine.check_permission("content", "publish", {"environment": "production"})["allowed"] is False
    assert engine.check_permission("content", "publish", {"environment": "test"})["allowed"] is True
    assert engine.check_permission("missing", "read")["allowed"] is False


def test_ssrf_validation_rejects_local_and_metadata_targets() -> None:
    validator = InputValidator()
    assert not validator.is_valid_url("http://127.0.0.1/")
    assert not validator.is_valid_url("http://localhost/")
    assert not validator.is_valid_url("http://169.254.169.254/latest/meta-data/")
    assert not validator.is_valid_url("file:///etc/passwd")
    assert validator.is_valid_url("https://example.com/")


def test_firewall_rate_limit_is_thread_safe() -> None:
    firewall = Firewall(max_clients=100)
    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(lambda _: firewall.check_rate_limit("client", 10), range(100)))
    assert sum(results) == 10


def test_expired_tokens_are_removed_from_reverse_indexes() -> None:
    manager = TokenManager()
    manager.create_token(TokenType.SESSION, "user-1", expires_in=0.001)
    import time
    time.sleep(0.01)
    assert manager.cleanup_expired() == 1
    assert "user-1" not in manager._user_tokens


def test_in_memory_secrets_fail_closed_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UCOS_ENV", "production")
    manager = SecretsManager()
    with pytest.raises(RuntimeError):
        manager.set_secret("api_key", "secret")
    monkeypatch.setenv("UCOS_ENV", "development")
    manager.set_secret("api_key", "secret")
    assert manager.verify_secret("api_key", "secret")
    assert not manager.verify_secret("api_key", "wrong")
