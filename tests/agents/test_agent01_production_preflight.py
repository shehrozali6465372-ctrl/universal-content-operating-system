"""Read-only readiness gate tests for Agent 01."""
from __future__ import annotations

from types import SimpleNamespace

from scripts.agent01_production_preflight import run_preflight


class Registry:
    def get(self, account_id):
        return SimpleNamespace(account_id=account_id, platform="pinterest", niche="home decor", enabled=True)


class Store:
    def __init__(self, baseline, history):
        self.baseline = baseline
        self.history = history

    def history_baseline(self, account_id, kind):
        return self.baseline

    def get(self, account_id, kind, key, default=None):
        return self.history if key == "collection:execution_history" else default


class Database:
    _postgresql_available = True
    _pool = object()


def test_preflight_uses_keyless_real_provider_and_requires_verified_history_baseline():
    report = run_preflight(
        "acct-1",
        registry=Registry(),
        store=Store(None, []),
        database=Database(),
        environment={},
    )

    assert report["status"] == "blocked"
    assert report["checks"]["research_provider"]["status"] == "pass"
    assert report["checks"]["research_provider"]["reason_code"] == "gdelt_keyless_fallback_selected"
    assert report["checks"]["history_baseline"]["status"] == "blocked"
    assert report["production_certified"] is False
    assert report["side_effects"] == {
        "external_search_performed": False,
        "content_published": False,
    }


def test_preflight_passes_only_when_all_prerequisites_are_visible():
    report = run_preflight(
        "acct-1",
        registry=Registry(),
        store=Store({
            "status": "complete",
            "source": "operator_review",
            "records_checked": 1,
            "verified_at": "2026-10-14T10:00:00+00:00",
            "coverage": "Verified account history",
        }, [{"topic": "Known post", "published": True}]),
        database=Database(),
        environment={"TAVILY_API_KEY": "not-returned-to-report"},
    )

    assert report["status"] == "ready_for_live_smoke"
    assert all(check["status"] == "pass" for check in report["checks"].values())
    assert "not-returned-to-report" not in str(report)


def test_preflight_rejects_unreadable_history_even_when_baseline_exists():
    report = run_preflight(
        "acct-1",
        registry=Registry(),
        store=Store({"status": "complete"}, None),
        database=Database(),
        environment={"TAVILY_API_KEY": "redacted"},
    )
    assert report["status"] == "blocked"
    assert report["checks"]["account_history"]["reason_code"] == "history_missing_or_invalid"



def test_preflight_rejects_status_only_history_marker():
    report = run_preflight(
        "acct-1",
        registry=Registry(),
        store=Store({"status": "complete"}, []),
        database=Database(),
        environment={"TAVILY_API_KEY": "redacted"},
    )
    assert report["status"] == "blocked"
    assert report["checks"]["history_baseline"]["reason_code"] == "history_baseline_metadata_invalid"
    assert report["production_certified"] is False
    assert report["side_effects"]["external_search_performed"] is False
