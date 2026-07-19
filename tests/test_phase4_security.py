"""Tests for Phase 4 — Security (13 modules)."""
from __future__ import annotations
import time
import pytest

# ─── Authentication ────────────────────────────────────────────────
from layers.layer17_security.modules.authentication.authentication import AuthenticationManager

class TestAuthentication:
    def setup_method(self):
        self.am = AuthenticationManager()

    def test_register_authenticate(self):
        self.am.register_user("ali", "ali@test.com", "pass123")
        session = self.am.authenticate_password("ali", "pass123")
        assert session is not None
        assert session.user_id is not None

    def test_wrong_password(self):
        self.am.register_user("ali", "ali@test.com", "pass123")
        session = self.am.authenticate_password("ali", "wrong")
        assert session is None

    def test_api_key(self):
        user = self.am.register_user("ali")
        assert self.am.register_api_key(user.user_id, "key123")
        assert self.am.authenticate_api_key("key123") == user.user_id

    def test_lockout(self):
        self.am.register_user("ali", "ali@test.com", "pass123")
        for _ in range(5):
            self.am.authenticate_password("ali", "wrong")
        user = self.am.get_user(self.am.list_users()[0]["user_id"])
        assert not user.is_active

    def test_invalidate_session(self):
        self.am.register_user("ali", "", "pass123")
        session = self.am.authenticate_password("ali", "pass123")
        assert self.am.invalidate_session(session.session_id)

    def test_stats(self):
        self.am.register_user("ali", "", "pass123")
        stats = self.am.stats()
        assert stats["users"] == 1


# ─── Authorization ─────────────────────────────────────────────────
from layers.layer17_security.modules.authorization.authorization import AuthorizationManager, Permission

class TestAuthorization:
    def setup_method(self):
        self.am = AuthorizationManager()

    def test_create_role(self):
        role = self.am.create_role("admin", {Permission.READ, Permission.WRITE, Permission.ADMIN})
        assert role.name == "admin"

    def test_assign_role(self):
        role = self.am.create_role("admin", {Permission.READ})
        assert self.am.assign_role("user1", role.role_id)
        assert self.am.has_permission("user1", Permission.READ)
        assert not self.am.has_permission("user1", Permission.WRITE)

    def test_revoke_role(self):
        role = self.am.create_role("admin", {Permission.READ})
        self.am.assign_role("user1", role.role_id)
        assert self.am.revoke_role("user1", role.role_id)
        assert not self.am.has_permission("user1", Permission.READ)


# ─── Permission Engine ─────────────────────────────────────────────
from layers.layer17_security.modules.permission_engine.permission_engine import PermissionEngine

class TestPermissionEngine:
    def setup_method(self):
        self.pe = PermissionEngine()

    def test_add_check(self):
        self.pe.add_rule("content", "read", "allow")
        result = self.pe.check_permission("content", "read")
        assert result["allowed"]

    def test_deny(self):
        self.pe.add_rule("content", "delete", "deny")
        result = self.pe.check_permission("content", "delete")
        assert not result["allowed"]

    def test_no_rule(self):
        result = self.pe.check_permission("unknown", "read")
        assert not result["allowed"]

    def test_role_permissions(self):
        self.pe.assign_role_permissions("admin", ["read", "write", "delete"])
        assert self.pe.check_role_permission("admin", "read")
        assert not self.pe.check_role_permission("user", "read")


# ─── Token Manager ────────────────────────────────────────────────
from layers.layer17_security.modules.token_manager.token_manager import TokenManager, TokenType

class TestTokenManager:
    def setup_method(self):
        self.tm = TokenManager()

    def test_create_validate(self):
        token = self.tm.create_token(TokenType.API_KEY, "user1")
        assert self.tm.validate_token(token.token_value) is not None

    def test_revoke(self):
        token = self.tm.create_token(TokenType.BEARER, "user1")
        assert self.tm.revoke_token(token.token_value)
        assert self.tm.validate_token(token.token_value) is None

    def test_revoke_all_user(self):
        self.tm.create_token(TokenType.API_KEY, "user1")
        self.tm.create_token(TokenType.API_KEY, "user1")
        count = self.tm.revoke_all_user_tokens("user1")
        assert count == 2

    def test_cleanup_expired(self):
        token = self.tm.create_token(TokenType.SESSION, "user1", expires_in=0.01)
        time.sleep(0.02)
        assert self.tm.cleanup_expired() == 1

    def test_stats(self):
        self.tm.create_token(TokenType.API_KEY, "user1")
        stats = self.tm.stats()
        assert stats["total"] == 1


# ─── Encryption Engine ─────────────────────────────────────────────
from layers.layer17_security.modules.encryption_engine.encryption_engine import EncryptionEngine

class TestEncryptionEngine:
    def setup_method(self):
        self.ee = EncryptionEngine()
        self.ee.set_key("test-key-123")

    def test_encrypt_decrypt(self):
        encrypted = self.ee.encrypt("hello world")
        decrypted = self.ee.decrypt(encrypted)
        assert decrypted == "hello world"

    def test_hash(self):
        h = self.ee.hash("test")
        assert len(h) == 64

    def test_hmac(self):
        sig = self.ee.hmac_sign("message")
        assert self.ee.hmac_verify("message", sig)
        assert not self.ee.hmac_verify("tampered", sig)

    def test_generate_key(self):
        key = self.ee.generate_key()
        assert len(key) == 64


# ─── Input Validator ───────────────────────────────────────────────
from layers.layer17_security.modules.input_validator.input_validator import InputValidator, ValidationRule

class TestInputValidator:
    def setup_method(self):
        self.iv = InputValidator()
        self.iv.add_rule("email", ValidationRule("email", self.iv.is_valid_email, "Invalid email"))
        self.iv.add_rule("name", ValidationRule("required", lambda v: bool(v), "Name required"))

    def test_valid(self):
        result = self.iv.validate({"email": "a@test.com", "name": "Ali"})
        assert result["valid"]

    def test_invalid(self):
        result = self.iv.validate({"email": "bad", "name": ""})
        assert not result["valid"]
        assert len(result["errors"]) == 2

    def test_sanitize(self):
        result = self.iv.sanitize_string("<script>alert('xss')</script>test")
        assert "<script>" not in result
        assert "test" in result

    def test_validate_field(self):
        result = self.iv.validate_field("email", "valid@test.com")
        assert result["valid"]


# ─── Output Sanitizer ──────────────────────────────────────────────
from layers.layer17_security.modules.output_sanitizer.output_sanitizer import OutputSanitizer

class TestOutputSanitizer:
    def setup_method(self):
        self.os = OutputSanitizer()

    def test_sanitize_html(self):
        result = self.os.sanitize_html("<b>hello</b><script>alert(1)</script>")
        assert "<script>" not in result

    def test_sanitize_dict(self):
        result = self.os.sanitize_dict({"name": "<b>Ali</b>", "age": 30})
        assert "<b>" not in result["name"]
        assert result["age"] == 30


# ─── Firewall ──────────────────────────────────────────────────────
from layers.layer17_security.modules.firewall.firewall import Firewall

class TestFirewall:
    def setup_method(self):
        self.fw = Firewall()

    def test_block_ip(self):
        self.fw.block_ip("1.2.3.4")
        assert self.fw.is_ip_blocked("1.2.3.4")
        result = self.fw.evaluate("1.2.3.4", "/api")
        assert not result["allowed"]

    def test_rate_limit(self):
        for _ in range(100):
            assert self.fw.check_rate_limit("client1", max_requests=100)
        assert not self.fw.check_rate_limit("client1", max_requests=100)

    def test_path_block(self):
        self.fw.block_path("/admin")
        result = self.fw.evaluate("1.2.3.4", "/admin")
        assert not result["allowed"]

    def test_allow(self):
        result = self.fw.evaluate("1.2.3.4", "/api")
        assert result["allowed"]


# ─── Secrets Manager ──────────────────────────────────────────────
from layers.layer17_security.modules.secrets_manager.secrets_manager import SecretsManager

class TestSecretsManager:
    def setup_method(self):
        self.sm = SecretsManager()

    def test_set_get(self):
        self.sm.set_secret("db_pass", "secret123", "database")
        assert self.sm.get_secret("db_pass") == "secret123"

    def test_rotate(self):
        self.sm.set_secret("key", "old")
        assert self.sm.rotate_secret("key", "new")
        assert self.sm.get_secret("key") == "new"

    def test_delete(self):
        self.sm.set_secret("key", "val")
        assert self.sm.delete_secret("key")
        assert self.sm.get_secret("key") is None

    def test_list(self):
        self.sm.set_secret("a", "1", "db")
        self.sm.set_secret("b", "2", "api")
        assert len(self.sm.list_secrets("db")) == 1


# ─── Audit Logger ─────────────────────────────────────────────────
from layers.layer17_security.modules.audit_logger.audit_logger import AuditLogger, AuditSeverity

class TestAuditLogger:
    def setup_method(self):
        self.al = AuditLogger()

    def test_log(self):
        event = self.al.log("login", AuditSeverity.INFO, "User logged in")
        assert event.event_type == "login"

    def test_query(self):
        self.al.log("login", AuditSeverity.INFO, "msg", user_id="u1")
        self.al.log("logout", AuditSeverity.WARNING, "msg", user_id="u1")
        results = self.al.query(user_id="u1")
        assert len(results) == 2


# ─── Security Policies ────────────────────────────────────────────
from layers.layer17_security.modules.security_policies.security_policies import SecurityPolicies, PolicyLevel

class TestSecurityPolicies:
    def setup_method(self):
        self.sp = SecurityPolicies()

    def test_create_evaluate(self):
        policy = self.sp.create_policy("password", PolicyLevel.HIGH)
        policy.add_rule("min_length", lambda ctx: len(ctx.get("password", "")) >= 8)
        result = self.sp.evaluate_all({"password": "longpass"})
        assert result["all_passed"]

    def test_violation(self):
        policy = self.sp.create_policy("password", PolicyLevel.HIGH)
        policy.add_rule("min_length", lambda ctx: len(ctx.get("password", "")) >= 8)
        result = self.sp.evaluate_all({"password": "short"})
        assert not result["all_passed"]


# ─── Signature Engine ──────────────────────────────────────────────
from layers.layer17_security.modules.signature_engine.signature_engine import SignatureEngine

class TestSignatureEngine:
    def setup_method(self):
        self.se = SignatureEngine()
        self.se.generate_key("key1")

    def test_sign_verify(self):
        sig = self.se.sign("key1", "data")
        assert self.se.verify("key1", "data", sig)
        assert not self.se.verify("key1", "tampered", sig)

    def test_remove_key(self):
        assert self.se.remove_key("key1")
        assert "key1" not in self.se.list_keys()


# ─── JWT Framework ─────────────────────────────────────────────────
from layers.layer17_security.modules.jwt_framework.jwt_framework import JWTFramework

class TestJWTFramework:
    def setup_method(self):
        self.jwt = JWTFramework("test-secret")

    def test_create_decode(self):
        token = self.jwt.create_token({"sub": "user1", "role": "admin"})
        payload = self.jwt.decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user1"

    def test_revoke(self):
        token = self.jwt.create_token({"sub": "user1"})
        self.jwt.revoke_token(token)
        assert self.jwt.decode_token(token) is None

    def test_refresh(self):
        token = self.jwt.create_token({"sub": "user1"})
        new_token = self.jwt.refresh_token(token)
        assert new_token is not None
        payload = self.jwt.decode_token(new_token)
        assert payload["sub"] == "user1"

    def test_invalid_token(self):
        assert self.jwt.decode_token("invalid.token.here") is None
