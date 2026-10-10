from types import SimpleNamespace

from services.ucos_browser import server


class _Cursor:
    def __init__(self, calls):
        self.calls = calls

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, params=None):
        self.calls.append((sql, params))


class _Connection:
    def __init__(self, calls):
        self.calls = calls

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def cursor(self):
        return _Cursor(self.calls)


def test_browser_audit_stores_only_minimal_metadata(monkeypatch):
    calls = []
    connection = _Connection(calls)
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/ignored")
    monkeypatch.setitem(
        __import__("sys").modules,
        "psycopg",
        SimpleNamespace(connect=lambda _dsn, connect_timeout: connection),
    )

    server._record_task_run(
        "task-1",
        {
            "profile_ref": "test-profile",
            "url": "https://example.com/path?access_token=DO_NOT_STORE",
            "page_text": "DO_NOT_STORE",
        },
        "completed",
        result={
            "final_url": "https://example.org/private/path?token=DO_NOT_STORE",
            "persistent_profile": True,
        },
        duration_ms=42,
    )

    assert len(calls) == 2
    ddl, insert = calls
    assert "CREATE TABLE IF NOT EXISTS browser_task_runs" in ddl[0]
    assert "INSERT INTO browser_task_runs" in insert[0]
    assert insert[1] == (
        "task-1",
        "test-profile",
        "example.com",
        "example.org",
        "completed",
        42,
        True,
        None,
    )
    assert "DO_NOT_STORE" not in repr(calls)
