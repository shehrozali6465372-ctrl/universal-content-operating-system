"""Real production evidence gate for UCOS Agent 01.

Runs against the configured production Neon database, real Pinterest APIs, and the
real research provider through the authenticated deployed UCOS API. No mocked adapters, canned API responses, injected stores, or
publishing calls are used. This is live validation evidence, not an automatic
production certificate: the release orchestrator must also be wired and verified.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REQUIRED_ENV = (
    "NEON_DATABASE_URL",
    "UCOS_CREDENTIAL_ENCRYPTION_KEY",
)


def _call_deployed_api_smoke(account_id: str, *, dispatch_mode: str) -> dict[str, Any]:
    """Call the authenticated deployed UCOS API; retry only while the route is not deployed."""
    root_key = str(os.environ.get("UCOS_CREDENTIAL_ENCRYPTION_KEY") or "").strip()
    if not root_key:
        return {
            "status": "failed_live_smoke",
            "reason_code": "certification_signing_key_missing",
            "request_path_verified": False,
            "external_search_performed": False,
            "content_published": False,
        }
    base_url = str(os.environ.get("UCOS_API_BASE_URL") or "https://ucos-backend.onrender.com").strip().rstrip("/")
    body = json.dumps({
        "account_id": account_id,
        "mode": dispatch_mode,
        "limit": 1,
    }, separators=(",", ":"), sort_keys=True).encode("utf-8")
    endpoint = f"{base_url}/agents/AG01/research"

    for attempt in range(36):
        timestamp = str(int(time.time()))
        nonce = secrets.token_hex(16)
        derived_key = hmac.new(
            root_key.encode("utf-8"),
            b"UCOS_AGENT01_DISPATCH_API_V1",
            hashlib.sha256,
        ).digest()
        canonical = (
            f"POST\n/agents/AG01/research\n{timestamp}\n{nonce}\n"
            f"{hashlib.sha256(body).hexdigest()}"
        ).encode("utf-8")
        signature = hmac.new(derived_key, canonical, hashlib.sha256).hexdigest()
        request = Request(
            endpoint,
            data=body,
            headers={
                "X-UCOS-Agent01-Timestamp": timestamp,
                "X-UCOS-Agent01-Nonce": nonce,
                "X-UCOS-Agent01-Signature": signature,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=180) as response:
                status_code = int(getattr(response, "status", 200))
                raw = response.read(1_000_000)
        except HTTPError as exc:
            status_code = int(exc.code)
            raw = exc.read(100_000)
            if status_code == 404 and b"Endpoint not found" in raw and attempt < 35:
                time.sleep(5)
                continue
            try:
                wrapper = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                wrapper = {}
            data = wrapper.get("data") if isinstance(wrapper, dict) else None
            return dict(data) if isinstance(data, dict) else {
                "status": "failed_live_smoke",
                "reason_code": f"deployed_api_http_{status_code}",
                "request_path_verified": False,
                "external_search_performed": False,
                "content_published": False,
            }
        except TimeoutError:
            # The endpoint runs real research and Neon read-back; do not retry a
            # timed-out POST because the first request may still be executing.
            return {
                "status": "failed_live_smoke",
                "reason_code": "deployed_api_request_timeout",
                "request_path_verified": False,
                "external_search_performed": False,
                "content_published": False,
            }
        except URLError as exc:
            if isinstance(getattr(exc, "reason", None), TimeoutError):
                return {
                    "status": "failed_live_smoke",
                    "reason_code": "deployed_api_request_timeout",
                    "request_path_verified": False,
                    "external_search_performed": False,
                    "content_published": False,
                }
            if attempt < 35:
                time.sleep(5)
                continue
            return {
                "status": "failed_live_smoke",
                "reason_code": "deployed_api_unreachable",
                "request_path_verified": False,
                "external_search_performed": False,
                "content_published": False,
            }
        except OSError:
            if attempt < 35:
                time.sleep(5)
                continue
            return {
                "status": "failed_live_smoke",
                "reason_code": "deployed_api_unreachable",
                "request_path_verified": False,
                "external_search_performed": False,
                "content_published": False,
            }

        try:
            wrapper = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {
                "status": "failed_live_smoke",
                "reason_code": "deployed_api_invalid_json",
                "request_path_verified": False,
                "external_search_performed": False,
                "content_published": False,
            }
        if not isinstance(wrapper, dict):
            return {
                "status": "failed_live_smoke",
                "reason_code": "deployed_api_invalid_response",
                "request_path_verified": False,
                "external_search_performed": False,
                "content_published": False,
            }
        data = wrapper.get("data")
        if status_code >= 400:
            return dict(data) if isinstance(data, dict) else {
                "status": "failed_live_smoke",
                "reason_code": f"deployed_api_http_{status_code}",
                "request_path_verified": True,
                "external_search_performed": False,
                "content_published": False,
            }
        if not isinstance(data, dict):
            return {
                "status": "failed_live_smoke",
                "reason_code": "deployed_api_missing_result",
                "request_path_verified": True,
                "external_search_performed": False,
                "content_published": False,
            }
        return {**data, "request_path_verified": True, "dispatch_mode": dispatch_mode}

    return {
        "status": "failed_live_smoke",
        "reason_code": "deployed_agent01_endpoint_not_ready",
        "request_path_verified": False,
        "external_search_performed": False,
        "content_published": False,
    }


def _agent01_manifest_status() -> str:
    try:
        manifest = json.loads(Path("agents/manifest.json").read_text(encoding="utf-8"))
        for agent in manifest.get("agents", []):
            if isinstance(agent, dict) and str(agent.get("id") or "").upper() == "AG01":
                return str(agent.get("status") or "unknown").strip().lower()
    except (OSError, json.JSONDecodeError):
        pass
    return "unknown"


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

    # Exercise the deployed HTTP request path. Use certification mode until the
    # manifest is explicitly production_ready; after certification, exercise normal
    # production dispatch through the same authenticated endpoint.
    dispatch_mode = "production" if _agent01_manifest_status() == "production_ready" else "certification"

    live_reports: list[dict[str, Any]] = []
    for account in accounts:
        report = _call_deployed_api_smoke(str(account.account_id), dispatch_mode=dispatch_mode)
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
            "checks": safe_checks,
            "external_search_performed": bool(report.get("external_search_performed", False)),
            "content_published": bool(report.get("content_published", False)),
            "reason_code": report.get("reason_code"),
            "request_path_verified": bool(report.get("request_path_verified", False)),
            "dispatch_mode": str(report.get("dispatch_mode") or dispatch_mode),
        })

    live_passed = all(
        item["status"] == "passed_live_smoke" and item["request_path_verified"]
        for item in live_reports
    )
    production_certified = live_passed and dispatch_mode == "production"
    return {
        "status": (
            "production_certified" if production_certified else
            "passed_real_live_validation" if live_passed else "failed_live_validation"
        ),
        "enabled_pinterest_account_count": len(accounts),
        "history_imports": import_reports,
        "live_smokes": live_reports,
        "external_research_performed": any(item["external_search_performed"] for item in live_reports),
        "content_published": False,
        "production_certified": production_certified,
        "dispatch_mode": dispatch_mode,
        "remaining_release_gate": (
            "No AG01 live gate remains; continue to the next agent only after the production certificate is reviewed."
            if production_certified else
            "Set AG01 manifest status to production_ready after the authenticated API request path and Neon read-back have passed."
            if live_passed else
            "Fix the deployed API request path or Neon read-back failure before certification."
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
    return 0 if report.get("status") in {"passed_real_live_validation", "production_certified"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
