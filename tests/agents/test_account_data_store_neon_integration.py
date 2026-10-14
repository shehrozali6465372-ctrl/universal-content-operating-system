"""Live PostgreSQL integration test for production account-scoped persistence.

CI supplies a disposable PostgreSQL 16 service. The test uses the real L13
manager and verifies that parallel account-event appends do not lose writes.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from uuid import uuid4

import pytest

from layers.layer07_publishing.modules.account_control.account_data_store import (
    AccountDataStore,
    _account_level,
)
from layers.layer13_persistence.modules.postgresql.manager import PostgreSQLManager


class RegistryStub:
    def get(self, account_id):
        return SimpleNamespace(account_id=account_id)


def test_neon_account_store_round_trip_and_concurrent_append(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    database = PostgreSQLManager()
    try:
        if not database.initialize() or not database._postgresql_available:
            pytest.skip("Disposable PostgreSQL service is unavailable")
    except Exception as exc:
        database.close()
        pytest.skip(f"Disposable PostgreSQL service could not initialize: {type(exc).__name__}")

    account_id = "agent01-test-" + uuid4().hex
    level = _account_level(account_id)
    store = AccountDataStore(registry=RegistryStub(), database=database)
    events = [{"sequence": i, "account_id": account_id} for i in range(24)]
    try:
        store.put(account_id, "content", "agent01-roundtrip", {"state": "ready"})
        assert store.get(account_id, "content", "agent01-roundtrip") == {"state": "ready"}

        with ThreadPoolExecutor(max_workers=6) as executor:
            list(executor.map(
                lambda event: store.append(account_id, "content", "agent01-events", event),
                events,
            ))

        stored = store.get(account_id, "content", "collection:agent01-events", default=[])
        assert len(stored) == len(events)
        assert {item["sequence"] for item in stored} == set(range(24))
        assert all(item["account_id"] == account_id for item in stored)
        assert store.snapshot(account_id, "content")["agent01-roundtrip"] == {"state": "ready"}
    finally:
        try:
            database._pool.delete("agent_memory", "level = %s", (level,))
        finally:
            database.close()
