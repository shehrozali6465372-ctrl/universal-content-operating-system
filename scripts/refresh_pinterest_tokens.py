"""Scheduled refresh of Pinterest OAuth credentials in the UCOS L13 Neon vault.

Run from the repository root in a dedicated Render Cron Job. Secrets must be
configured as Render environment variables; never pass token values on CLI.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone, timedelta

from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
from layers.layer13_persistence.modules.postgresql.repositories.credential_repository import CredentialRepository
from layers.layer14_enterprise_integration.modules.api_gateway.api_gateway import APIGateway

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("pinterest-token-refresh")

# Daily execution with a 72-hour look-ahead refreshes well before access expiry.
REFRESH_WINDOW_SECONDS = 72 * 60 * 60


def main() -> int:
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

    checked = refreshed = failures = 0
    now = datetime.now(timezone.utc)

    for account in accounts:
        if not account.credentials_ref or not account.platform_account_id:
            continue
        try:
            credentials = repository.get_for_account(
                account.credentials_ref, account.account_id, include_expired=True
            )
            if not credentials:
                logger.info("account=%s state=no_active_credential", account.account_id)
                continue
            if not credentials.get("expires_at"):
                logger.warning("account=%s state=missing_expiry_metadata", account.account_id)
                continue
            expiry = datetime.fromisoformat(str(credentials["expires_at"]).replace("Z", "+00:00"))
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            if expiry > now + timedelta(seconds=REFRESH_WINDOW_SECONDS):
                continue

            checked += 1
            prior_expiry = expiry.isoformat()
            gateway._refresh_pinterest_token_if_needed(
                account, credentials, client_id, client_secret,
                refresh_window_seconds=REFRESH_WINDOW_SECONDS,
            )
            refreshed += 1
            logger.info("account=%s state=refresh_succeeded prior_expiry=%s", account.account_id, prior_expiry)
        except Exception as exc:
            failures += 1
            logger.error("account=%s state=refresh_failed error_type=%s", account.account_id, type(exc).__name__)

    logger.info("Pinterest refresh run complete checked=%d refreshed=%d failures=%d", checked, refreshed, failures)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
