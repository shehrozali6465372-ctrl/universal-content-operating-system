# UCOS Personal Browser Session Persistence

## Purpose

The worker can persist the browser's Playwright storage state (cookies and origin-scoped localStorage) in Postgres so an authentication session can be restored after a process restart. Snapshots are encrypted in the worker before they reach the database using Fernet authenticated encryption.

The snapshot does **not** contain page text, screenshots, passwords typed into forms, open tabs, browsing history, sessionStorage, or arbitrary browser-profile files. Sites can still expire or revoke cookies, require re-authentication, or bind sessions to device/browser signals.

## Required configuration for database-backed durability

Configure these environment variables on the `ucos-personal-browser` Render service:

- `UCOS_BROWSER_STATE_DATABASE_URL`: a dedicated Neon Postgres connection string for encrypted browser session snapshots. This variable takes precedence and avoids changing the application’s existing database configuration. If it is absent, the service falls back to `DATABASE_URL`.
- `UCOS_BROWSER_STATE_ENCRYPTION_KEY`: a Fernet key generated in a trusted terminal with:
  ```bash
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
  Save it as a Render secret/environment variable. Never commit the key or store it in the database.
- `UCOS_BROWSER_REQUIRE_DURABLE_PROFILE=true`: requires either an explicitly configured persistent profile directory or a configured encrypted database store. If durable storage is unavailable, profile creation fails closed instead of silently falling back to ephemeral storage.

The database table `browser_profile_states` is created on demand. It stores an encrypted blob keyed by `profile_ref`, plus an update timestamp. The same encryption key must remain available to decrypt existing rows. Rotating the key without re-encrypting or deleting saved rows will intentionally fail closed.

## Validation required before certification

1. Confirm the service has the database and encryption-key variables without displaying either secret.
2. Use a test profile to log in to a permitted site, verify a snapshot was written, restart/redeploy the service, and confirm that the same profile restores the session.
3. Confirm a wrong/missing encryption key returns a clear failure and never stores an unencrypted snapshot.
4. Test the actual affiliate site flow with an authorized account and verify the final affiliate URL through its official account flow.

A successful unit test proves the encryption and restore contract only. It does not, by itself, prove the Render service is configured, that an existing account session survives a live restart, or that an affiliate link is valid.
