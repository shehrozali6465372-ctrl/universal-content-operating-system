"""Real production evidence gate for UCOS Agent 01.

Runs only against the configured production Neon database and real Pinterest and
Tavily APIs. No mocked adapters, canned API responses, injected stores, or
publishing calls are used. This is live validation evidence, not an automatic
production certificate: the release orchestrator must also be wired and verified.
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Any


REQUIRED_ENV = (
    "NEON_DATABASE_URL",
    "UCOS_CREDENTIAL_ENCRYPTION_KEY",
)


def run_gate(*, max_pages: int = 100) -> dict[str, Any]:
    """Import account-local Pinterest history, then run a real one-topic smoke per account."""
    if os.environ.get("APP_ENV", "").strip().lower() not in {"production", "prod"}:
        return {
            "status": "blocked",
            "reason_code": "APP_ENV_must_be_production",
            "history_imports": [],
            "live_smokes": [],
            "production_certified": False,
        }

    missing = [name for name in REQUIRED_ENV if not str(os.environ.get(name) or "").strip()]
    if missing:
        return {
            "status": "blocked",
            "reason_code": "required_live_environment_missing",
            "missing_environment_names": missing,
            "history_imports": [],
            "live_smokes": [],
            "production_certified": False,
            "external_research_performed": False,
            "content_published": False,
        }

    try:
        from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry

        registry = AccountRegistry()
        accounts = registry.list(platform="pinterest", enabled_only=True)
    except Exception as exc:
        return {
            "status": "failed",
            "reason_code": f"production_account_registry_{type(exc).__name__}",
            "history_imports": [],
            "live_smokes": [],
            "production_certified": False,
            "external_research_performed": False,
            "content_published": False,
        }

    if not accounts:
        return {
            "status": "blocked",
            "reason_code": "no_enabled_pinterest_accounts_found",
            "history_imports": [],
            "live_smokes": [],
            "production_certified": False,
            "external_research_performed": False,
            "content_published": False,
        }

    from scripts.agent01_import_pinterest_history import run_import

    import_reports: list[dict[str, Any]] = []
    for account in accounts:
        report = run_import(
            str(account.account_id),
            confirmed=True,
            max_pages=max_pages,
        )
        import_reports.append({
            "status": report.get("status", "unknown"),
            "identity_verified": bool(report.get("identity_verified", False)),
            "api_records_checked": int(report.get("api_records_checked") or 0),
            "new_history_records_added": int(report.get("new_history_records_added") or 0),
            "history_baseline_marked_complete": bool(report.get("history_baseline_marked_complete", False)),
            "reason_code": report.get("reason_code"),
        })

    # Never make paid research calls if any account history failed import or
    # readback. No baseline should be assumed complete for a partially imported account.
    imports_passed = all(
        item["status"] == "completed"
        and item["identity_verified"]
        and item["history_baseline_marked_complete"]
        for item in import_reports
    )
    if not imports_passed:
        return {
            "status": "failed_history_import",
            "enabled_pinterest_account_count": len(accounts),
            "history_imports": import_reports,
            "live_smokes": [],
            "external_research_performed": False,
            "content_published": False,
            "production_certified": False,
        }

    from scripts.agent01_live_smoke import run_live_smoke

    live_reports: list[dict[str, Any]] = []
    for account in accounts:
        report = run_live_smoke(str(account.account_id))
        checks = report.get("checks", {})
        safe_checks = {
            str(name): {
                "status": str(detail.get("status") or "unknown"),
                **(
                    {"count": int(detail.get("count") or 0)}
                    if isinstance(detail, dict) and "count" in detail else {}
                ),
                **(
                    {"request_count": int(detail.get("request_count") or 0)}
                    if isinstance(detail, dict) and "request_count" in detail else {}
                ),
            }
            for name, detail in checks.items()
            if isinstance(detail, dict)
        } if isinstance(checks, dict) else {}
        live_reports.append({
            "status": str(report.get("status") or "unknown"),
            "agent_id": str(report.get("agent_id") or "AG01"),
            "research_provider": str(report.get("research_provider") or "unknown"),
            "checks": safe_checks,
            "external_search_performed": bool(report.get("external_search_performed", False)),
            "content_published": bool(report.get("content_published", False)),
            "reason_code": report.get("reason_code"),
        })

    live_passed = all(item["status"] == "passed_live_smoke" for item in live_reports)
    return {
        "status": "passed_real_live_validation" if live_passed else "failed_live_validation",
        "enabled_pinterest_account_count": len(accounts),
        "history_imports": import_reports,
        "live_smokes": live_reports,
        "external_research_performed": any(item["external_search_performed"] for item in live_reports),
        "content_published": False,
        "production_certified": False,
        "remaining_release_gate": (
            "Wire AG01 into the real UCOS release orchestrator and verify the deployed request-to-Neon path."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-pages", type=int, default=100, help="Maximum Pinterest pages per account (1–1000)")
    args = parser.parse_args(argv)
    if isinstance(args.max_pages, bool) or not 1 <= args.max_pages <= 1000:
        parser.error("--max-pages must be between 1 and 1000")
    report = run_gate(max_pages=args.max_pages)
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0 if report.get("status") == "passed_real_live_validation" else 2


if __name__ == "__main__":
    raise SystemExit(main())
