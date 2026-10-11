"""Scheduled refresh of Pinterest OAuth credentials in the UCOS L13 Neon vault.

Run from the repository root in a dedicated Render Cron Job. Secrets must be
configured as Render environment variables; never pass token values on CLI.
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, unquote

# A script launched as `python scripts/refresh_pinterest_tokens.py` gets the
# scripts/ directory as sys.path[0], not the repository root. Add the root so
# UCOS layer packages resolve consistently in GitHub Actions and Render jobs.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
from layers.layer13_persistence.modules.postgresql.repositories.credential_repository import CredentialRepository
from layers.layer14_enterprise_integration.modules.api_gateway.api_gateway import APIGateway

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("pinterest-token-refresh")

# Daily execution with a 72-hour look-ahead refreshes well before access expiry.
REFRESH_WINDOW_SECONDS = 72 * 60 * 60


def main() -> int:
    database_url = os.getenv("NEON_DATABASE_URL", "").strip()
    if database_url:
        parsed = urlparse(database_url)
        if parsed.scheme not in {"postgres", "postgresql"} or not parsed.hostname or not parsed.path.strip("/"):
            logger.error("NEON_DATABASE_URL is not a valid PostgreSQL URL")
            return 2
        os.environ["POSTGRES_HOST"] = parsed.hostname
        os.environ["POSTGRES_PORT"] = str(parsed.port or 5432)
        os.environ["POSTGRES_DB"] = unquote(parsed.path.lstrip("/"))
        os.environ["POSTGRES_USER"] = unquote(parsed.username or "")
        os.environ["POSTGRES_PASSWORD"] = unquote(parsed.password or "")
    elif not all(os.getenv(name, "").strip() for name in ("POSTGRES_HOST", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")):
        logger.error("NEON_DATABASE_URL or complete POSTGRES_* connection settings are required")
        return 2

    client_id = os.getenv("PINTEREST_CLIENT_ID", "").strip()
    client_secret = os.getenv("PINTEREST_CLIENT_SECRET", "").strip()
    encryption_key = os.getenv("UCOS_CREDENTIAL_ENCRYPTION_KEY", "").strip()
    if not all((client_id, client_secret, encryption_key)):
        logger.error("Required Pinterest client credentials or L13 encryption key are not configured")
        return 2

    try:
        accounts = AccountRegistry().list(platform="pinterest", enabled_only=True)
        repository = CredentialRepository(encryption_key=encryption_key)
        gateway = APIGateway(host="127.0.0.1", port=8000)
    except Exception as exc:
        logger.error("Pinterest refresh job initialization failed (%s)", type(exc).__name__)
        return 2

    accounts_seen = credentials_found = due = refreshed = failures = skipped = 0
    now = datetime.now(timezone.utc)
    logger.info("Pinterest refresh scan started enabled_accounts=%d refresh_window_hours=%d", len(accounts), REFRESH_WINDOW_SECONDS // 3600)

    for account in accounts:
        accounts_seen += 1
        if not account.credentials_ref or not account.platform_account_id:
            skipped += 1
            logger.warning("account=%s state=skipped_missing_credential_identity", account.account_id)
            continue
        try:
            credentials = repository.get_for_account(
                account.credentials_ref, account.account_id, include_expired=True
            )
            if not credentials:
                skipped += 1
                logger.warning("account=%s state=no_active_credential", account.account_id)
                continue
            credentials_found += 1
            if not credentials.get("expires_at"):
                skipped += 1
                logger.warning("account=%s state=missing_expiry_metadata", account.account_id)
                continue
            expiry = datetime.fromisoformat(str(credentials["expires_at"]).replace("Z", "+00:00"))
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            hours_until_expiry = (expiry - now).total_seconds() / 3600
            if expiry > now + timedelta(seconds=REFRESH_WINDOW_SECONDS):
                logger.info("account=%s state=not_due hours_until_expiry=%.1f", account.account_id, hours_until_expiry)
                continue

            due += 1
            prior_expiry = expiry.isoformat()
            gateway._refresh_pinterest_token_if_needed(
                account, credentials, client_id, client_secret,
                refresh_window_seconds=REFRESH_WINDOW_SECONDS,
            )
            # Verify persistence by reading back encrypted vault metadata only.
            # Do not emit access or refresh token values into logs.
            persisted = repository.get_for_account(
                account.credentials_ref, account.account_id, include_expired=True
            )
            if not persisted or not persisted.get("expires_at"):
                raise RuntimeError("refreshed credential metadata was not persisted")
            persisted_expiry = datetime.fromisoformat(str(persisted["expires_at"]).replace("Z", "+00:00"))
            if persisted_expiry.tzinfo is None:
                persisted_expiry = persisted_expiry.replace(tzinfo=timezone.utc)
            if persisted_expiry <= expiry:
                raise RuntimeError("credential expiry did not advance after refresh")
            refreshed += 1
            logger.info("account=%s state=refresh_succeeded prior_expiry=%s new_expiry=%s", account.account_id, prior_expiry, persisted_expiry.isoformat())
        except Exception as exc:
            failures += 1
            logger.error("account=%s state=refresh_failed error_type=%s", account.account_id, type(exc).__name__)

    logger.info(
        "Pinterest refresh run complete accounts_seen=%d credentials_found=%d due=%d refreshed=%d skipped=%d failures=%d",
        accounts_seen, credentials_found, due, refreshed, skipped, failures,
    )
    if not accounts_seen:
        logger.error("No enabled Pinterest accounts found in canonical Neon identity tables")
        return 2
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
