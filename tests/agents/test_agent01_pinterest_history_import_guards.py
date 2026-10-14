"""Guard tests for the real Pinterest history importer.

These tests ensure real production writes cannot start without explicit operator
confirmation and the production environment. They do not substitute fake API responses.
"""
from __future__ import annotations

import pytest

from scripts.agent01_import_pinterest_history import run_import


def test_live_history_import_requires_explicit_confirmation(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")

    report = run_import("account-real", confirmed=False)

    assert report["status"] == "blocked"
    assert report["reason_code"] == "explicit_live_import_confirmation_required"
    assert report["history_baseline_marked_complete"] is False


def test_live_history_import_refuses_nonproduction_even_when_confirmed(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")

    report = run_import("account-real", confirmed=True)

    assert report["status"] == "blocked"
    assert report["reason_code"] == "APP_ENV_must_be_production"
    assert report["history_baseline_marked_complete"] is False


def test_live_history_import_rejects_unbounded_pagination_before_network(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")

    with pytest.raises(ValueError, match="max_pages"):
        run_import("account-real", confirmed=True, max_pages=0)
