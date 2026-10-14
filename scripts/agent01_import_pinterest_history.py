"""Import real Pinterest Pins into an account's UCOS duplicate-check history.

Production-only and explicitly confirmed. This calls the actual Pinterest API v5
with the selected account's encrypted Neon credential. No mock client or fallback
credential is accepted. The history baseline is marked complete only after all
pages are fetched and persisted rows are read back successfully.
"""
from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_BASE = "https://api.pinterest.com/v5"
PAGE_SIZE = 250
DEFAULT_MAX_PAGES = 100
MAX_ALLOWED_PAGES = 1000


class PinterestHistoryImportError(RuntimeError):
    """A safe, non-secret error raised when history import cannot be completed."""


def _api_get(path: str, access_token: str, timeout: float = 20.0) -> dict[str, Any]:
    request = Request(
        f"{API_BASE}{path}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(8_000_000)
        value = json.loads(raw.decode("utf-8"))
    except HTTPError as exc:
        raise PinterestHistoryImportError(f"pinterest_http_{int(exc.code)}") from None
    except URLError as exc:
        reason = getattr(exc, "reason", None)
        code = "timeout" if isinstance(reason, TimeoutError) else "network_error"
        raise PinterestHistoryImportError(f"pinterest_{code}") from None
    except TimeoutError:
        raise PinterestHistoryImportError("pinterest_timeout") from None
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise PinterestHistoryImportError("pinterest_invalid_json") from None
    except OSError:
        raise PinterestHistoryImportError("pinterest_network_error") from None
    if not isinstance(value, dict):
        raise PinterestHistoryImportError("pinterest_response_contract_invalid")
    return value


def _identity_matches(profile: Mapping[str, Any], external_account_id: str) -> bool:
    expected = str(external_account_id or "").strip().casefold()
    if not expected:
        return False
    observed = {
        str(profile.get("id") or "").strip().casefold(),
        str(profile.get("username") or "").strip().casefold(),
    }
    observed.discard("")
    return expected in observed


def _fetch_all_pins(access_token: str, max_pages: int) -> list[dict[str, Any]]:
    pins: list[dict[str, Any]] = []
    seen_pin_ids: set[str] = set()
    bookmark = ""
    seen_bookmarks: set[str] = set()

    for page_number in range(1, max_pages + 1):
        query = {"page_size": PAGE_SIZE}
        if bookmark:
            query["bookmark"] = bookmark
        response = _api_get(f"/pins?{urlencode(query)}", access_token)
        items = response.get("items")
        if not isinstance(items, list):
            raise PinterestHistoryImportError("pinterest_pins_response_missing_items")
        for item in items:
            if not isinstance(item, Mapping):
                raise PinterestHistoryImportError("pinterest_pin_record_invalid")
            pin_id = str(item.get("id") or "").strip()
            if not pin_id:
                raise PinterestHistoryImportError("pinterest_pin_id_missing")
            if pin_id in seen_pin_ids:
                continue
            seen_pin_ids.add(pin_id)
            pins.append(dict(item))

        next_bookmark = str(response.get("bookmark") or "").strip()
        if not next_bookmark:
            return pins
        if next_bookmark in seen_bookmarks or next_bookmark == bookmark:
            raise PinterestHistoryImportError("pinterest_pagination_loop_detected")
        seen_bookmarks.add(next_bookmark)
        bookmark = next_bookmark

    # Never set the history marker when the server indicates that pages remain.
    raise PinterestHistoryImportError("pinterest_pagination_limit_reached")


def run_import(
    account_id: str,
    *,
    confirmed: bool = False,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> dict[str, Any]:
    """Fetch real Pins and merge their history into the specific production account."""
    account_id = str(account_id or "").strip()
    if not account_id:
        raise ValueError("account_id is required")
    if not confirmed:
        return {
            "status": "blocked",
            "reason_code": "explicit_live_import_confirmation_required",
            "account_id": account_id,
            "history_baseline_marked_complete": False,
        }
    if os.environ.get("APP_ENV", "").strip().lower() not in {"production", "prod"}:
        return {
            "status": "blocked",
            "reason_code": "APP_ENV_must_be_production",
            "account_id": account_id,
            "history_baseline_marked_complete": False,
        }
    if isinstance(max_pages, bool) or not isinstance(max_pages, int) or not 1 <= max_pages <= MAX_ALLOWED_PAGES:
        raise ValueError(f"max_pages must be between 1 and {MAX_ALLOWED_PAGES}")

    try:
        from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
        from layers.layer07_publishing.modules.account_control.account_data_store import (
            AccountDataStore,
            is_verified_history_baseline,
        )
        from layers.layer17_security.modules.credential_resolver.credential_resolver import AccountCredentialResolver

        registry = AccountRegistry()
        account = registry.get(account_id)
        if account is None:
            raise PinterestHistoryImportError("account_not_registered")
        if not bool(getattr(account, "enabled", False)):
            raise PinterestHistoryImportError("account_disabled")
        if str(getattr(account, "platform", "") or "").strip().lower() != "pinterest":
            raise PinterestHistoryImportError("only_pinterest_accounts_supported")
        credentials_ref = str(getattr(account, "credentials_ref", "") or "").strip()
        external_account_id = str(getattr(account, "external_account_id", "") or "").strip()
        if not credentials_ref or not external_account_id:
            raise PinterestHistoryImportError("account_credential_reference_or_external_id_missing")

        credentials = AccountCredentialResolver.resolve(credentials_ref, account_id)
        access_token = str(credentials.get("access_token") or "").strip()
        if not access_token:
            raise PinterestHistoryImportError("account_credential_unavailable_or_decryption_failed")

        # Verify that this account-scoped token belongs to the configured Pinterest identity.
        profile = _api_get("/user_account", access_token)
        if not _identity_matches(profile, external_account_id):
            raise PinterestHistoryImportError("pinterest_identity_mismatch")

        pins = _fetch_all_pins(access_token, max_pages=max_pages)
        store = AccountDataStore(registry=registry)
        current = store.get(account_id, "content", "collection:execution_history", default=[])
        if current is None:
            current = []
        if not isinstance(current, list) or any(not isinstance(row, Mapping) for row in current):
            raise PinterestHistoryImportError("existing_execution_history_invalid")

        known_ids = {
            str(row.get("post_id") or "").strip()
            for row in current
            if str(row.get("platform") or "pinterest").strip().lower() == "pinterest"
            and str(row.get("post_id") or "").strip()
        }
        imported_at = datetime.now(timezone.utc).isoformat()
        new_records: list[dict[str, Any]] = []
        for pin in pins:
            pin_id = str(pin["id"]).strip()
            if pin_id in known_ids:
                continue
            title = str(pin.get("title") or "").strip()[:500]
            description = str(pin.get("description") or "").strip()[:20000]
            created_at = str(pin.get("created_at") or "").strip()[:64]
            new_records.append({
                "platform": "pinterest",
                "post_id": pin_id,
                "topic": title or description[:500] or f"Pinterest Pin {pin_id}",
                "title": title,
                "text": description,
                "content": description,
                "published": True,
                "published_at": created_at,
                "url": f"https://www.pinterest.com/pin/{pin_id}/",
                "history_source": "pinterest_api_v5",
                "history_imported_at": imported_at,
            })
            known_ids.add(pin_id)

        # Append only unseen Pin IDs so a sequential rerun does not add duplicates.
        # If interrupted, no completeness marker is written; a later rerun resumes safely.
        for row in new_records:
            store.append(account_id, "content", "execution_history", row)
        if not current and not pins:
            # An authenticated, fully paginated empty response is valid history too.
            store.put(account_id, "content", "collection:execution_history", [])

        saved_history = store.get(account_id, "content", "collection:execution_history", default=None)
        if not isinstance(saved_history, list) or any(not isinstance(row, Mapping) for row in saved_history):
            raise PinterestHistoryImportError("execution_history_readback_invalid")
        saved_ids = {
            str(row.get("post_id") or "").strip()
            for row in saved_history
            if str(row.get("platform") or "pinterest").strip().lower() == "pinterest"
        }
        missing_ids = {str(pin["id"]).strip() for pin in pins} - saved_ids
        if missing_ids:
            raise PinterestHistoryImportError("execution_history_readback_incomplete")

        marker = store.mark_history_baseline_verified(
            account_id,
            source="platform_api_import",
            records_checked=len(pins),
            confirmed=True,
        )
        saved_marker = store.history_baseline(account_id, "content")
        if not is_verified_history_baseline(saved_marker):
            raise PinterestHistoryImportError("history_baseline_readback_failed")

        return {
            "status": "completed",
            "account_id": account_id,
            "platform": "pinterest",
            "identity_verified": True,
            "api_records_checked": len(pins),
            "new_history_records_added": len(new_records),
            "history_records_after_import": len(saved_history),
            "history_baseline_marked_complete": True,
            "baseline_source": marker.get("source"),
            "note": "Only Pins returned by the authorized account's Pinterest API are covered; verify any off-platform or non-Pinterest history separately.",
        }
    except PinterestHistoryImportError as exc:
        return {
            "status": "blocked",
            "account_id": account_id,
            "reason_code": str(exc),
            "history_baseline_marked_complete": False,
        }
    except Exception as exc:
        # Never include exception text: it could contain credential or database details.
        return {
            "status": "failed",
            "account_id": account_id,
            "reason_code": f"history_import_exception_{type(exc).__name__}",
            "history_baseline_marked_complete": False,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account-id", required=True, help="Registered Pinterest account ID, never a secret")
    parser.add_argument("--confirm-live-import", action="store_true", help="Confirm fetching live Pinterest history and appending it to Neon")
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES, help=f"Maximum Pinterest pages; 1–{MAX_ALLOWED_PAGES}")
    args = parser.parse_args(argv)
    report = run_import(
        args.account_id,
        confirmed=args.confirm_live_import,
        max_pages=args.max_pages,
    )
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0 if report.get("status") == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
