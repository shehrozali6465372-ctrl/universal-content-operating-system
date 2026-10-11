"""Tests for encrypted, Neon-backed browser session snapshots."""
import sys
from types import SimpleNamespace

import pytest

from services.ucos_browser import profile_persistence as persistence
from services.ucos_browser import server as browser_server


class _Cursor:
    def __init__(self, rows):
        self.rows = rows
        self.result = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, params=None):
        statement = " ".join(sql.lower().split())
        if "select encrypted_state" in statement:
            self.result = (
                (self.rows[params[0]],) if params[0] in self.rows else None
            )
        elif "select 1 from browser_profile_states" in statement:
            self.result = (1,) if params[0] in self.rows else None
        elif "insert into browser_profile_states" in statement:
            self.rows[params[0]] = bytes(params[1])
            self.result = None
        else:
            self.result = None

    def fetchone(self):
        return self.result


class _Connection:
    def __init__(self, rows):
        self.rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def cursor(self):
        return _Cursor(self.rows)


class _FakeBrowserContext:
    def __init__(self):
        self.cookies = []
        self.scripts = []

    def add_cookies(self, cookies):
        self.cookies.extend(cookies)

    def add_init_script(self, script=None, path=None):
        self.scripts.append(script)


@pytest.fixture
def encrypted_store(monkeypatch):
    cryptography = pytest.importorskip("cryptography.fernet")
    key = cryptography.Fernet.generate_key().decode("ascii")
    rows = {}
    connection = _Connection(rows)
    monkeypatch.setenv("DATABASE_URL", "postgresql://test.invalid/test")
    monkeypatch.setenv("UCOS_BROWSER_STATE_ENCRYPTION_KEY", key)
    monkeypatch.setenv("UCOS_BROWSER_REQUIRE_DURABLE_PROFILE", "true")
    monkeypatch.setitem(
        sys.modules,
        "psycopg",
        SimpleNamespace(connect=lambda _dsn, connect_timeout: connection),
    )
    return rows, key


def test_encrypted_session_state_round_trips_without_plaintext(encrypted_store):
    rows, _key = encrypted_store
    state = {
        "cookies": [{
            "name": "session",
            "value": "secret-cookie-value",
            "domain": ".example.test",
            "path": "/",
            "expires": -1,
            "httpOnly": True,
            "secure": True,
            "sameSite": "Lax",
        }],
        "origins": [{
            "origin": "https://example.test",
            "localStorage": [
                {"name": "access", "value": "secret-local-storage-value"},
                {"name": persistence._RESTORE_MARKER, "value": "1"},
            ],
        }],
    }

    assert persistence.save_profile_state("account-1", state) is True
    encrypted = rows["account-1"]
    assert b"secret-cookie-value" not in encrypted
    assert b"secret-local-storage-value" not in encrypted
    restored = persistence.load_profile_state("account-1")
    assert restored == {
        "cookies": state["cookies"],
        "origins": [{
            "origin": "https://example.test",
            "localStorage": [{"name": "access", "value": "secret-local-storage-value"}],
        }],
    }
    assert persistence.has_profile_state("account-1") is True
    assert persistence.has_profile_state("missing") is False


def test_wrong_encryption_key_fails_closed(encrypted_store, monkeypatch):
    persistence.save_profile_state(
        "account-1",
        {"cookies": [{"name": "sid", "value": "sensitive"}], "origins": []},
    )
    cryptography = pytest.importorskip("cryptography.fernet")
    monkeypatch.setenv(
        "UCOS_BROWSER_STATE_ENCRYPTION_KEY",
        cryptography.Fernet.generate_key().decode("ascii"),
    )
    with pytest.raises(RuntimeError, match="could not be decrypted"):
        persistence.load_profile_state("account-1")


def test_local_storage_restore_is_origin_scoped_and_script_safe():
    context = _FakeBrowserContext()
    state = {
        "cookies": [{"name": "sid", "value": "secret", "domain": ".example.test", "path": "/"}],
        "origins": [{
            "origin": "https://example.test",
            "localStorage": [{"name": "x", "value": "</script><script>alert(1)</script>"}],
        }],
    }
    persistence.restore_storage_state(context, state)
    assert context.cookies == state["cookies"]
    assert len(context.scripts) == 1
    assert "sessionStorage.getItem(marker)" in context.scripts[0]
    assert "</script>" not in context.scripts[0]
    assert "https://example.test" in context.scripts[0]


def test_required_mode_without_database_and_encryption_key_fails_closed(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("UCOS_BROWSER_STATE_ENCRYPTION_KEY", raising=False)
    monkeypatch.setenv("UCOS_BROWSER_REQUIRE_DURABLE_PROFILE", "true")
    assert persistence.is_configured() is False
    with pytest.raises(RuntimeError, match="requires DATABASE_URL"):
        persistence.load_profile_state("account-1")


def test_optional_mode_without_store_does_not_claim_persistence(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("UCOS_BROWSER_STATE_ENCRYPTION_KEY", raising=False)
    monkeypatch.setenv("UCOS_BROWSER_REQUIRE_DURABLE_PROFILE", "false")
    assert persistence.is_configured() is False
    assert persistence.load_profile_state("account-1") is None
    assert persistence.save_profile_state(
        "account-1", {"cookies": [], "origins": []}
    ) is False


def test_writable_default_profile_directory_is_not_certified_as_durable(monkeypatch, tmp_path):
    monkeypatch.delenv("UCOS_BROWSER_PROFILE_DIR", raising=False)
    monkeypatch.delenv("UCOS_BROWSER_REQUIRE_DURABLE_PROFILE", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("UCOS_BROWSER_STATE_ENCRYPTION_KEY", raising=False)
    original_path = browser_server.Path
    monkeypatch.setattr(
        browser_server,
        "Path",
        lambda value: tmp_path if str(value) == "/var/data/ucos-browser/profiles" else original_path(value),
    )
    path, persistent = browser_server._profile_dir("account-1")
    assert path.startswith(str(tmp_path))
    assert persistent is False
