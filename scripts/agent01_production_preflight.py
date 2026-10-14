"""Read-only preflight for UCOS Agent 01 production prerequisites.

This command checks configuration and account-state readiness. It does not call
Tavily, create content, or publish. A green preflight still requires a separate
live source smoke test and deployed end-to-end evidence before certification.
"""
from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping
from typing import Any


def run_preflight(
    account_id: str,
    *,
    registry: Any = None,
    store: Any = None,
    database: Any = None,
    environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Return a sanitized readiness report; never returns connection details or key values."""
    account_id = str(account_id or "").strip()
    if not account_id:
        raise ValueError("account_id is required")
    env = environment if environment is not None else os.environ
    checks: dict[str, dict[str, str]] = {}

    try:
        if registry is None:
            from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
            registry = AccountRegistry()
        account = registry.get(account_id)
        if account is None:
            checks["account"] = {"status": "blocked", "reason_code": "account_not_registered"}
        elif not bool(getattr(account, "enabled", False)):
            checks["account"] = {"status": "blocked", "reason_code": "account_disabled"}
        elif not str(getattr(account, "platform", "") or "").strip() or not str(getattr(account, "niche", "") or "").strip():
            checks["account"] = {"status": "blocked", "reason_code": "account_platform_or_niche_missing"}
        else:
            checks["account"] = {"status": "pass", "reason_code": "registered_enabled"}
    except Exception:
        checks["account"] = {"status": "unknown", "reason_code": "account_registry_unavailable"}

    try:
        if database is None:
            from layers.layer13_persistence.modules.postgresql.manager import get_database
            database = get_database()
        if bool(getattr(database, "_postgresql_available", False)) and getattr(database, "_pool", None) is not None:
            checks["neon_postgresql"] = {"status": "pass", "reason_code": "postgresql_pool_available"}
        else:
            checks["neon_postgresql"] = {"status": "blocked", "reason_code": "postgresql_unavailable"}
    except Exception:
        checks["neon_postgresql"] = {"status": "unknown", "reason_code": "postgresql_check_failed"}

    checks["tavily_api_key"] = {
        "status": "pass" if str(env.get("TAVILY_API_KEY") or "").strip() else "blocked",
        "reason_code": "configured" if str(env.get("TAVILY_API_KEY") or "").strip() else "tavily_api_key_missing",
    }

    try:
        from layers.layer07_publishing.modules.account_control.account_data_store import (
            AccountDataStore,
            is_verified_history_baseline,
        )
        if store is None:
            if registry is None:
                from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
                registry = AccountRegistry()
            store = AccountDataStore(registry=registry)
        marker = store.history_baseline(account_id, "content") if hasattr(store, "history_baseline") else store.get(
            account_id, "memory", "history_baseline:content:v1", default=None
        )
        if is_verified_history_baseline(marker):
            checks["history_baseline"] = {"status": "pass", "reason_code": "verified_with_provenance"}
        else:
            marker_status = str(marker.get("status") or "missing") if isinstance(marker, Mapping) else "missing"
            reason_code = (
                "history_baseline_metadata_invalid"
                if isinstance(marker, Mapping) and marker_status == "complete"
                else f"history_baseline_{marker_status}"
            )
            checks["history_baseline"] = {"status": "blocked", "reason_code": reason_code}
    except Exception:
        checks["history_baseline"] = {"status": "unknown", "reason_code": "history_baseline_unavailable"}

    try:
        if store is None:
            raise RuntimeError("account data store unavailable")
        history = store.get(account_id, "content", "collection:execution_history", default=None)
        if isinstance(history, list) and all(isinstance(row, Mapping) for row in history):
            checks["account_history"] = {"status": "pass", "reason_code": "history_readable"}
        else:
            checks["account_history"] = {"status": "blocked", "reason_code": "history_missing_or_invalid"}
    except Exception:
        checks["account_history"] = {"status": "unknown", "reason_code": "history_read_failed"}

    ready = all(item.get("status") == "pass" for item in checks.values())
    return {
        "agent_id": "AG01",
        "account_id": account_id,
        "status": "ready_for_live_smoke" if ready else "blocked",
        "production_certified": False,
        "checks": checks,
        "next_step": (
            "Run a bounded live Tavily smoke and verify the deployed Agent 01 end-to-end path."
            if ready else
            "Resolve the blocked/unknown checks; do not enable production dispatch."
        ),
        "side_effects": {"external_search_performed": False, "content_published": False},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account-id", required=True, help="Registered UCOS account ID (never a secret)")
    args = parser.parse_args(argv)
    report = run_preflight(args.account_id)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "ready_for_live_smoke" else 2


if __name__ == "__main__":
    raise SystemExit(main())
