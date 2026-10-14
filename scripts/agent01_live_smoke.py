"""Run a real, bounded Agent 01 smoke against configured production dependencies.

This command dispatches the real AG01 implementation through AgentDispatcher and uses the selected real research provider plus durable Neon/PostgreSQL storage. It refuses external research until the target account and verified account-history baseline are available. It never publishes.

A pass is live-smoke evidence only, not a production certificate.
"""
from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping
from typing import Any


def _summary(report: Mapping[str, Any]) -> dict[str, Any]:
    candidates = report.get("candidates")
    if not isinstance(candidates, list):
        candidates = []
    candidate_summaries = []
    for row in candidates:
        if not isinstance(row, Mapping):
            continue
        candidate_summaries.append({
            "decision": str(row.get("decision") or "unknown"),
            "evidence_count": int(row.get("evidence_count") or 0),
            "independent_source_count": int(row.get("independent_source_count") or 0),
            "persistence": row.get("persistence") if isinstance(row.get("persistence"), Mapping) else {},
        })
    return {
        "agent_id": "AG01",
        "run_id": str(report.get("run_id") or ""),
        "agent_status": str(report.get("status") or "unknown"),
        "source_status": str(
            (report.get("research_sources") or {}).get("status", "unknown")
            if isinstance(report.get("research_sources"), Mapping) else "unknown"
        ),
        "candidate_count": len(candidate_summaries),
        "candidates": candidate_summaries,
        "report_persistence": (
            report.get("persistence")
            if isinstance(report.get("persistence"), Mapping) else {}
        ),
        "publishing_performed": bool(
            (report.get("publishing") or {}).get("performed", False)
            if isinstance(report.get("publishing"), Mapping) else False
        ),
    }


def run_live_smoke(account_id: str, *, dispatch_mode: str = "certification") -> dict[str, Any]:
    """Use the deployed environment's real provider and durable store; never certify."""
    if os.environ.get("APP_ENV", "").strip().lower() not in {"production", "prod"}:
        return {
            "status": "blocked",
            "reason_code": "APP_ENV_must_be_production",
            "production_certified": False,
            "external_search_performed": False,
            "content_published": False,
        }

    from scripts.agent01_production_preflight import run_preflight

    preflight = run_preflight(account_id)
    if preflight.get("status") != "ready_for_live_smoke":
        return {
            "status": "blocked",
            "reason_code": "production_preflight_blocked",
            "preflight": preflight,
            "production_certified": False,
            "external_search_performed": False,
            "content_published": False,
        }

    # Imports occur only after preflight so that missing history never triggers a
    # real search. The agent uses its real selected provider and real account store.
    request_count = 0
    report: dict[str, Any] = {}
    try:
        from agents.dispatcher import AgentDispatcher
        from layers.layer07_publishing.modules.account_control.account_data_store import AccountDataStore
        from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry

        report = AgentDispatcher().dispatch(
            "AG01",
            constructor_kwargs={"account_id": account_id},
            input_payload={"limit": 1},
            mode=dispatch_mode,
        )
        summary = _summary(report)
        source_status = report.get("research_sources") if isinstance(report.get("research_sources"), Mapping) else {}
        request_count = int(source_status.get("request_count") or 0)
        if source_status.get("provider") not in {"tavily", "gdelt_context"}:
            return {
                "status": "blocked",
                "reason_code": "live_research_source_not_configured",
                "production_certified": False,
                "external_search_performed": request_count > 0,
                "content_published": False,
            }
        registry = AccountRegistry()
        store = AccountDataStore(registry=registry)
        run_id = summary["run_id"]
        durable_run = store.get(
            account_id, "memory", f"research_agent_run:{run_id}", default=None
        )
        snapshot = store.snapshot(account_id, "memory")
        saved_candidates = [
            value for key, value in snapshot.items()
            if key.startswith("research_candidate:")
            and isinstance(value, Mapping)
            and value.get("run_id") == run_id
        ]
        saved_evidence = [
            value for key, value in snapshot.items()
            if key.startswith("research_evidence:")
            and isinstance(value, Mapping)
            and value.get("run_id") == run_id
        ]
        ready_rows = [
            row for row in summary["candidates"]
            if row.get("decision") == "READY_FOR_VERIFICATION"
            and row.get("independent_source_count", 0) >= 2
            and row.get("persistence", {}).get("candidate_state") == "saved"
            and row.get("persistence", {}).get("evidence_state") == "saved"
        ]
        checks = {
            "real_provider_requests": {
                "status": "pass" if request_count > 0 else "fail",
                "request_count": request_count,
            },
            "research_candidate_eligible_for_agent_06": {
                "status": "pass" if len(ready_rows) == 1 else "fail",
                "count": len(ready_rows),
            },
            "durable_run_readback": {
                "status": "pass" if isinstance(durable_run, Mapping) else "fail",
            },
            "durable_candidate_readback": {
                "status": "pass" if len(saved_candidates) == 1 else "fail",
                "count": len(saved_candidates),
            },
            "durable_evidence_readback": {
                "status": "pass" if len(saved_evidence) >= 2 else "fail",
                "count": len(saved_evidence),
            },
            "report_persistence": {
                "status": "pass" if summary["report_persistence"].get("status") == "persisted" else "fail",
            },
            "no_publishing": {
                "status": "pass" if summary["publishing_performed"] is False else "fail",
            },
        }
        passed = all(check["status"] == "pass" for check in checks.values())
        return {
            "status": "passed_live_smoke" if passed else "failed_live_smoke",
            "agent_id": "AG01",
            "account_id": account_id,
            "agent_version": str(report.get("agent_version") or "unknown"),
            "checks": checks,
            "agent_report": summary,
            "production_certified": False,
            "external_search_performed": request_count > 0,
            "content_published": False,
            "next_step": (
                "Attach this live evidence to the release gate; certification still requires review of the full production path."
                if passed else
                "Fix the failed live check before enabling production dispatch."
            ),
        }
    except Exception as exc:
        # Error messages can contain connection details; report only the exception type.
        request_count = int(
            ((report.get("research_sources") or {}).get("request_count", 0))
            if isinstance(report.get("research_sources"), Mapping) else 0
        )
        return {
            "status": "failed_live_smoke",
            "reason_code": f"live_smoke_exception_{type(exc).__name__}",
            "provider_request_count": request_count,
            "production_certified": False,
            "external_search_performed": request_count > 0,
            "content_published": False,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account-id", required=True, help="Registered production account ID, never a secret")
    args = parser.parse_args(argv)
    report = run_live_smoke(args.account_id)
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0 if report.get("status") == "passed_live_smoke" else 2


if __name__ == "__main__":
    raise SystemExit(main())
