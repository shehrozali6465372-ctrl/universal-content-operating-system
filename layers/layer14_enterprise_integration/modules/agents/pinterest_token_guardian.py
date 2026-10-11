"""Long-running Pinterest Token Guardian for the UCOS API service.

Can run a scan at process startup and every hour. In the selected deployment,
GitHub Actions owns the hourly refresh schedule, so this in-process guardian can
be disabled to avoid duplicate scans and misleading configuration errors.
Credentials stay encrypted in the canonical Neon vault; tokens are never logged.
"""
from __future__ import annotations

import logging
import os
import threading
import time

logger = logging.getLogger("pinterest-token-guardian")
_guardian_thread = None
_guardian_lock = threading.Lock()
SCAN_INTERVAL_SECONDS = 60 * 60


def _run_forever() -> None:
    while True:
        started = time.monotonic()
        try:
            from scripts.refresh_pinterest_tokens import main as run_refresh_scan
            result = run_refresh_scan()
            if result:
                logger.error("Pinterest Token Guardian scan finished with protection gaps exit_code=%s", result)
            else:
                logger.info("Pinterest Token Guardian scan finished successfully")
        except Exception as exc:
            # Do not log exception text: drivers may embed connection information.
            logger.error("Pinterest Token Guardian scan crashed error_type=%s", type(exc).__name__)
        elapsed = time.monotonic() - started
        time.sleep(max(30, SCAN_INTERVAL_SECONDS - elapsed))


def start_pinterest_token_guardian() -> bool:
    """Start the worker unless an external scheduler owns refresh."""
    global _guardian_thread
    enabled = os.getenv("UCOS_PINTEREST_GUARDIAN_ENABLED", "true").strip().lower()
    if enabled not in {"1", "true", "yes", "on"}:
        logger.info("Pinterest Token Guardian disabled; external scheduler owns refresh")
        return False
    with _guardian_lock:
        if _guardian_thread is not None and _guardian_thread.is_alive():
            return False
        _guardian_thread = threading.Thread(
            target=_run_forever,
            name="pinterest-token-guardian",
            daemon=True,
        )
        _guardian_thread.start()
        logger.info("Pinterest Token Guardian started interval_seconds=%d", SCAN_INTERVAL_SECONDS)
        return True
