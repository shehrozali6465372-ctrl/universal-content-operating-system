"""Regression tests for authenticated browser profile health metadata."""
import importlib.util
import logging
import os
from pathlib import Path
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import HTTPServer


MODULE_PATH = Path(__file__).resolve().parents[1] / "services" / "ucos_browser" / "server.py"
SPEC = importlib.util.spec_from_file_location("ucos_browser_server_test_module", MODULE_PATH)
browser_server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(browser_server)


def _serve(monkeypatch):
    monkeypatch.setenv("UCOS_BROWSER_TOKEN", "test-token")
    server = HTTPServer(("127.0.0.1", 0), browser_server.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, f"http://127.0.0.1:{server.server_port}"


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
