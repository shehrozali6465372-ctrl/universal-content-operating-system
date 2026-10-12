"""Regression tests for authenticated browser profile health metadata."""
import importlib.util
import json
import logging
import os
from pathlib import Path
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen


MODULE_PATH = Path(__file__).resolve().parents[1] / "services" / "ucos_browser" / "server.py"
SPEC = importlib.util.spec_from_file_location("ucos_browser_server_test_module", MODULE_PATH)
browser_server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(browser_server)


def _serve(monkeypatch):
    monkeypatch.setenv("UCOS_BROWSER_TOKEN", "test-token")
    server = browser_server.ThreadingHTTPServer(("127.0.0.1", 0), browser_server.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, f"http://127.0.0.1:{server.server_port}"



def test_browser_tasks_run_on_one_playwright_thread(monkeypatch):
    observed_thread_ids = []
    lock = threading.Lock()

    def fake_browser_task(_payload):
        with lock:
            observed_thread_ids.append(threading.get_ident())
        return {"ok": True, "thread_id": threading.get_ident()}

    monkeypatch.setattr(browser_server, "_execute_task_on_browser_thread", fake_browser_task)

    def invoke(_):
        return browser_server.execute_task({"actions": []})["thread_id"]

    with __import__("concurrent.futures").futures.ThreadPoolExecutor(max_workers=6) as callers:
        results = list(callers.map(invoke, range(12)))

    assert len(results) == 12
    assert len(set(results)) == 1
    assert results[0] != threading.get_ident()
    assert len(set(observed_thread_ids)) == 1


def test_session_health_requires_authentication(monkeypatch):
    server, thread, base_url = _serve(monkeypatch)
    try:
        request = Request(base_url + "/session/health?profile_ref=account-1")
        try:
            urlopen(request, timeout=3)
        except HTTPError as exc:
            assert exc.code == 401
            assert b"authentication required" in exc.read()
        else:
            raise AssertionError("session health must reject unauthenticated requests")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_session_health_rejects_invalid_profile_ref(monkeypatch):
    server, thread, base_url = _serve(monkeypatch)
    try:
        request = Request(
            base_url + "/session/health?profile_ref=" + ("x" * 81),
            headers={"Authorization": "Bearer test-token"},
        )
        try:
            urlopen(request, timeout=3)
        except HTTPError as exc:
            assert exc.code == 400
            assert b"invalid or unavailable browser profile" in exc.read()
        else:
            raise AssertionError("invalid profile_ref must return HTTP 400")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


class _UnwritablePath:
    def __init__(self, value):
        self.value = value

    def __truediv__(self, other):
        return _UnwritablePath(self.value + "/" + str(other))

    def mkdir(self, *args, **kwargs):
        raise OSError("simulated unwritable persistent mount")

    def __str__(self):
        return self.value


def _force_default_profile_root_unwritable(monkeypatch):
    original_path = browser_server.Path
    monkeypatch.setattr(
        browser_server,
        "Path",
        lambda value: _UnwritablePath(value)
        if str(value) == "/var/data/ucos-browser/profiles"
        else original_path(value),
    )


def test_profile_dir_fails_closed_when_durable_storage_is_required(monkeypatch):
    monkeypatch.delenv("UCOS_BROWSER_PROFILE_DIR", raising=False)
    monkeypatch.setenv("UCOS_BROWSER_REQUIRE_DURABLE_PROFILE", "true")
    _force_default_profile_root_unwritable(monkeypatch)

    try:
        browser_server._profile_dir("account-1")
    except RuntimeError as exc:
        assert "durable browser profile storage is required" in str(exc)
    else:
        raise AssertionError("durability-required mode must reject ephemeral fallback")


def test_profile_dir_marks_ephemeral_fallback_non_persistent(monkeypatch):
    monkeypatch.delenv("UCOS_BROWSER_PROFILE_DIR", raising=False)
    monkeypatch.delenv("UCOS_BROWSER_REQUIRE_DURABLE_PROFILE", raising=False)
    _force_default_profile_root_unwritable(monkeypatch)
    monkeypatch.setattr(browser_server, "LOG", logging.getLogger("test"))
    path, persistent = browser_server._profile_dir("account-2")
    assert persistent is False
    assert path.startswith("/tmp/ucos-browser/profiles/")


def test_durable_profile_uses_encrypted_postgres_when_local_mount_is_unwritable(monkeypatch, caplog):
    monkeypatch.setattr(browser_server, "LOG", logging.getLogger("test"))
    monkeypatch.delenv("UCOS_BROWSER_PROFILE_DIR", raising=False)
    monkeypatch.setenv("UCOS_BROWSER_REQUIRE_DURABLE_PROFILE", "true")
    monkeypatch.setattr(browser_server.profile_persistence, "is_configured", lambda: True)
    _force_default_profile_root_unwritable(monkeypatch)

    with caplog.at_level(logging.INFO, logger="test"):
        path, disk_persistent = browser_server._profile_dir("account-durable")

    assert path.startswith("/tmp/ucos-browser/profiles/")
    assert disk_persistent is False
    assert "encrypted Postgres session snapshots" in caplog.text
    assert "browser profile storage" not in caplog.text


def test_session_health_does_not_treat_ephemeral_profile_files_as_durable(monkeypatch, tmp_path):
    profile_dir = tmp_path / "chromium-scratch"
    profile_dir.mkdir()
    (profile_dir / "Cookies").write_text("temporary", encoding="utf-8")

    monkeypatch.setattr(
        browser_server,
        "_profile_dir",
        lambda profile_ref: (str(profile_dir), False),
    )
    monkeypatch.setattr(browser_server.profile_persistence, "is_configured", lambda: True)
    monkeypatch.setattr(browser_server.profile_persistence, "has_profile_state", lambda profile_ref: False)

    server, thread, base_url = _serve(monkeypatch)
    try:
        request = Request(
            base_url + "/session/health?profile_ref=account-1",
            headers={"Authorization": "Bearer test-token"},
        )
        with urlopen(request, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload["status"] == "ok"
        assert payload["persistent"] is True
        assert payload["persistence_backend"] == "neon_postgres"
        assert payload["profile_initialized"] is False
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)

def test_startup_validation_decrypts_existing_profile_without_logging_session_values(monkeypatch, caplog):
    monkeypatch.setenv("UCOS_BROWSER_SESSION_SELF_TEST", "true")
    monkeypatch.setattr(browser_server.profile_persistence, "durable_required", lambda: True)
    monkeypatch.setattr(browser_server.profile_persistence, "self_test", lambda: True)
    monkeypatch.setattr(
        browser_server.profile_persistence,
        "load_profile_state",
        lambda profile_ref: {
            "cookies": [{"name": "session-cookie-secret", "value": "must-not-be-logged"}],
            "origins": [
                {
                    "origin": "https://example.com",
                    "localStorage": [
                        {"name": "private-key", "value": "must-not-be-logged"}
                    ],
                }
            ],
        },
    )

    with caplog.at_level(logging.INFO, logger="ucos.browser"):
        browser_server._run_profile_persistence_startup_self_test()

    assert "UCOS_BROWSER_SESSION_PERSISTENCE_SELF_TEST=PASS" in caplog.text
    assert "UCOS_BROWSER_EXISTING_PROFILE_SNAPSHOT=DECRYPTABLE" in caplog.text
    assert "profile_ref=amazon-primary" in caplog.text
    assert "cookie_count=1 origin_count=1" in caplog.text
    assert "must-not-be-logged" not in caplog.text
    assert "session-cookie-secret" not in caplog.text

def test_public_readyz_is_lightweight_and_does_not_require_token(monkeypatch):
    server, thread, base_url = _serve(monkeypatch)
    try:
        with urlopen(base_url + "/readyz", timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload == {"status": "ok", "service": "ucos-personal-browser"}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_readyz_responds_while_browser_execute_is_busy(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("UCOS_BROWSER_STATE_DATABASE_URL", raising=False)
    server, thread, base_url = _serve(monkeypatch)
    execute_started = threading.Event()
    allow_execute_finish = threading.Event()
    post_results = []

    def slow_execute(_payload):
        execute_started.set()
        if not allow_execute_finish.wait(timeout=4):
            raise RuntimeError("test execution timed out")
        return {"final_url": "https://example.com/", "persistent_profile": True}

    def post_execute():
        body = json.dumps({
            "profile_ref": "account-1",
            "url": "https://example.com/",
            "actions": [{"type": "screenshot"}],
        }).encode("utf-8")
        request = Request(
            base_url + "/execute",
            data=body,
            headers={
                "Authorization": "Bearer test-token",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=4) as response:
                post_results.append(response.status)
        except Exception as exc:
            post_results.append(type(exc).__name__)

    monkeypatch.setattr(browser_server, "execute_task", slow_execute)
    request_thread = threading.Thread(target=post_execute, daemon=True)
    try:
        request_thread.start()
        assert execute_started.wait(timeout=2), "execute request did not start"
        # This GET must be handled in a separate HTTP thread even while the
        # single Playwright worker slot is occupied by the simulated long task.
        with urlopen(base_url + "/readyz", timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert response.status == 200
        assert payload["status"] == "ok"
    finally:
        allow_execute_finish.set()
        request_thread.join(timeout=4)
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
    assert post_results == [200]


def test_startup_validation_fails_closed_when_saved_profile_cannot_be_decrypted(monkeypatch, caplog):
    monkeypatch.setenv("UCOS_BROWSER_SESSION_SELF_TEST", "true")
    monkeypatch.setattr(browser_server.profile_persistence, "durable_required", lambda: True)
    monkeypatch.setattr(browser_server.profile_persistence, "self_test", lambda: True)

    def fail_to_load(_profile_ref):
        raise RuntimeError("ciphertext unavailable")

    monkeypatch.setattr(browser_server.profile_persistence, "load_profile_state", fail_to_load)

    with caplog.at_level(logging.ERROR, logger="ucos.browser"):
        try:
            browser_server._run_profile_persistence_startup_self_test()
        except RuntimeError as exc:
            assert "saved profile could not be validated" in str(exc)
        else:
            raise AssertionError("required durable mode must fail closed on unreadable saved state")

    assert "UCOS_BROWSER_PERSISTENCE_STARTUP_VALIDATION=FAIL" in caplog.text
    assert "ciphertext unavailable" not in caplog.text

