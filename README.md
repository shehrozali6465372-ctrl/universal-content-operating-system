# UCOS Personal Browser

This repository is intentionally reduced to the standalone **UCOS Personal Browser** service.

## What remains

- Playwright-based browser worker and its web console in `services/ucos_browser/`
- Encrypted browser session persistence for PostgreSQL/Neon
- Browser-specific tests in `tests/`
- Browser-specific CI and live smoke workflows
- Browser session setup and persistence documentation

All other UCOS layers, agents, APIs, dashboards, providers, and unrelated services have been removed from the current `main` tree.

## Deployment

The existing Render service is expected to build from the repository root using:

- Dockerfile: `services/ucos_browser/Dockerfile`
- Runtime: `python services/ucos_browser/server.py`
- Requirements: `services/ucos_browser/requirements.txt`

Service URL: https://ucos-personal-browser.onrender.com

## Required environment

Configure these on the browser service in Render (never commit secret values):

- `UCOS_BROWSER_TOKEN` — required API bearer token
- `UCOS_BROWSER_STATE_DATABASE_URL` — dedicated PostgreSQL/Neon URL for browser session state (or `DATABASE_URL`)
- `UCOS_BROWSER_STATE_ENCRYPTION_KEY` — Fernet key used to encrypt persisted session state
- `UCOS_BROWSER_REQUIRE_DURABLE_PROFILE=true` — require durable session persistence when that is the intended production policy

The browser's session database and Render service are external resources and are not deleted by this repository cleanup.

## Local checks

```bash
pip install -r services/ucos_browser/requirements.txt pytest
playwright install chromium
PYTHONPATH=. pytest -q tests/test_ucos_personal_browser.py tests/test_browser_profile_persistence.py tests/test_browser_session_health_auth.py tests/test_browser_audit_storage.py
```

The CI workflow also performs a real Chromium smoke test against `https://example.com`.

## Security notes

The browser worker requires authentication for protected endpoints, blocks private/local network targets, and encrypts persisted session state. Keep production tokens, database URLs, and encryption keys in Render environment settings only.
