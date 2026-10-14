"""Production-adapter contract tests for the Neon-backed AccountDataStore."""
from __future__ import annotations

import json
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from layers.layer07_publishing.modules.account_control.account_data_store import (
    AccountDataStore,
    _account_level,
)


class FakeMemory:
    def __init__(self):
        self.values = {}

    def save(self, level, category, key, value, tags="", importance=0.5):
        self.values[(level, category, key)] = value
        return len(self.values)

    def load(self, level, category, key):
        return self.values.get((level, category, key))


class FakeCursor:
    def __init__(self, pool):
        self.pool = pool

    def execute(self, query, params=()):
        self.pool.statements.append((query, params))


class FakeConnection:
    def __init__(self, pool):
        self.pool = pool

    def cursor(self):
        return FakeCursor(self.pool)


class FakePool:
    def __init__(self, memory):
        self.memory = memory
        self.statements = []

    @contextmanager
    def transaction(self):
        yield FakeConnection(self)

    def query(self, query, params=()):
        level, category = params
        return [
            {"key": key, "value": value}
            for (row_level, row_category, key), value in self.memory.values.items()
            if row_level == level and row_category == category
        ]


class FakeDatabase:
    def __init__(self):
        self._postgresql_available = True
        self.memory = FakeMemory()
        self._pool = FakePool(self.memory)


class FakeRegistry:
    def get(self, account_id):
        return SimpleNamespace(account_id=account_id)


@pytest.fixture
def prod_store(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    db = FakeDatabase()
    return AccountDataStore(registry=FakeRegistry(), database=db), db


def test_account_namespaces_are_stable_and_isolated():
    assert _account_level("account-a") == _account_level("account-a")
    assert _account_level("account-a") != _account_level("account-b")
    assert len(_account_level("account-a")) <= 50


def test_production_put_get_and_snapshot_use_neon_memory(prod_store):
    store, db = prod_store
    store.put("account-a", "content", "brand", {"name": "A"})
    store.put("account-b", "content", "brand", {"name": "B"})

    assert store.get("account-a", "content", "brand") == {"name": "A"}
    assert store.get("account-b", "content", "brand") == {"name": "B"}
    assert store.get("account-a", "content", "missing", default="UNKNOWN") == "UNKNOWN"
    snapshot = store.snapshot("account-a", "content")
    assert snapshot == {"brand": {"name": "A"}}
    assert all(level.startswith("acct_") for level, _category, _key in db.memory.values)


def test_production_append_is_one_atomic_jsonb_upsert(prod_store):
    store, db = prod_store
    event = {"topic": "storage", "published": True}
    store.append("account-a", "content", "execution_history", event)

    assert len(db._pool.statements) == 1
    sql, params = db._pool.statements[0]
    assert "ON CONFLICT (level, category, key) DO UPDATE" in sql
    assert "agent_memory.value::jsonb || EXCLUDED.value::jsonb" in sql
    assert params[1] == "content"
    assert params[2] == "collection:execution_history"
    assert json.loads(params[3]) == [event]


def test_production_never_opens_local_sqlite(prod_store):
    store, _db = prod_store
    with pytest.raises(RuntimeError, match="disabled in production"):
        store._db("account-a", "content")


def test_unregistered_account_is_rejected(prod_store):
    store, _db = prod_store

    class MissingRegistry:
        def get(self, _account_id):
            return None

    store.registry = MissingRegistry()
    with pytest.raises(KeyError, match="unknown account_id"):
        store.get("missing", "content", "history")

def test_history_baseline_requires_explicit_confirmation(prod_store):
    store, _db = prod_store
    with pytest.raises(ValueError, match="confirmed=True"):
        store.mark_history_baseline_verified(
            "account-a", source="operator_review", records_checked=0
        )
    marker = store.mark_history_baseline_verified(
        "account-a", source="operator_review", records_checked=0, confirmed=True
    )
    assert marker["status"] == "complete"
    assert store.history_baseline("account-a") == marker
