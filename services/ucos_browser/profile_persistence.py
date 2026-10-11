"""Encrypted persistence for browser session cookies and localStorage.

Only Playwright storage_state fields needed to restore web sessions are saved.
Snapshots are authenticated-encrypted before they are written to Postgres.
Page text, screenshots, passwords, and raw browser-profile files are not stored.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS browser_profile_states (
    profile_ref TEXT PRIMARY KEY,
    encrypted_state BYTEA NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""
_RESTORE_MARKER = "__ucos_browser_storage_restored_v1"
_MAX_STATE_BYTES = 2_000_000


def durable_required() -> bool:
    return os.getenv("UCOS_BROWSER_REQUIRE_DURABLE_PROFILE", "false").strip().lower() in {
        "1", "true", "yes", "on"
    }


def is_configured() -> bool:
    return bool(
        os.getenv("DATABASE_URL", "").strip()
        and os.getenv("UCOS_BROWSER_STATE_ENCRYPTION_KEY", "").strip()
    )


def _fernet():
    key = os.getenv("UCOS_BROWSER_STATE_ENCRYPTION_KEY", "").strip()
    if not key:
        raise RuntimeError("browser session encryption key is not configured")
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:
        raise RuntimeError("cryptography package is required for browser session persistence") from exc
    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise RuntimeError("browser session encryption key has an invalid format") from exc


def _connect():
    dsn = os.getenv("DATABASE_URL", "").strip()
    if not dsn:
        raise RuntimeError("browser session database is not configured")
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError("psycopg package is required for browser session persistence") from exc
    try:
        return psycopg.connect(dsn, connect_timeout=3)
    except Exception as exc:
        raise RuntimeError(
            f"browser session database connection failed ({type(exc).__name__})"
        ) from None


def _ensure_table(cursor) -> None:
    cursor.execute(_TABLE_SQL)


def _normalise_state(state: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(state, dict):
        raise RuntimeError("browser session snapshot has an invalid format")
    cookies = state.get("cookies", [])
    origins = state.get("origins", [])
    if not isinstance(cookies, list) or not isinstance(origins, list):
        raise RuntimeError("browser session snapshot has an invalid format")
    normalized_origins = []
    for origin in origins:
        if not isinstance(origin, dict) or not isinstance(origin.get("origin"), str):
            continue
        entries = origin.get("localStorage", [])
        if not isinstance(entries, list):
            continue
        normalized_origins.append({
            "origin": origin["origin"],
            "localStorage": [
                entry for entry in entries
                if isinstance(entry, dict)
                and isinstance(entry.get("name"), str)
                and entry.get("name") != _RESTORE_MARKER
                and "value" in entry
            ],
        })
    return {"cookies": cookies, "origins": normalized_origins}


def load_profile_state(profile_ref: str) -> dict[str, Any] | None:
    if not is_configured():
        if durable_required():
            raise RuntimeError(
                "durable browser profile storage requires DATABASE_URL and UCOS_BROWSER_STATE_ENCRYPTION_KEY"
            )
        return None
    fernet = _fernet()
    try:
        with _connect() as connection:
            with connection.cursor() as cursor:
                _ensure_table(cursor)
                cursor.execute(
                    "SELECT encrypted_state FROM browser_profile_states WHERE profile_ref = %s",
                    (profile_ref,),
                )
                row = cursor.fetchone()
    except Exception as exc:
        raise RuntimeError(f"browser session database read failed ({type(exc).__name__})") from None
    if not row:
        return None
    try:
        decrypted = fernet.decrypt(bytes(row[0]))
    except Exception as exc:
        # Fernet's InvalidToken and malformed ciphertext must never cause a silent signed-out session.
        raise RuntimeError(
            "stored browser session state could not be decrypted; verify encryption key continuity"
        ) from None
    try:
        state = json.loads(decrypted.decode("utf-8"))
        return _normalise_state(state)
    except (ValueError, UnicodeDecodeError, TypeError) as exc:
        raise RuntimeError("stored browser session state is corrupt") from None


def save_profile_state(profile_ref: str, state: dict[str, Any]) -> bool:
    if not is_configured():
        if durable_required():
            raise RuntimeError(
                "durable browser profile storage requires DATABASE_URL and UCOS_BROWSER_STATE_ENCRYPTION_KEY"
            )
        return False
    clean_state = _normalise_state(state)
    payload = json.dumps(clean_state, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    if len(payload) > _MAX_STATE_BYTES:
        raise RuntimeError("browser session snapshot exceeds the 2 MB safety limit")
    encrypted = _fernet().encrypt(payload)
    try:
        with _connect() as connection:
            with connection.cursor() as cursor:
                _ensure_table(cursor)
                cursor.execute(
                    """
                    INSERT INTO browser_profile_states (profile_ref, encrypted_state, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (profile_ref) DO UPDATE SET
                        encrypted_state = EXCLUDED.encrypted_state,
                        updated_at = NOW()
                    """,
                    (profile_ref, encrypted),
                )
    except Exception as exc:
        raise RuntimeError(f"browser session database write failed ({type(exc).__name__})") from None
    return True


def has_profile_state(profile_ref: str) -> bool:
    if not is_configured():
        return False
    try:
        with _connect() as connection:
            with connection.cursor() as cursor:
                _ensure_table(cursor)
                cursor.execute(
                    "SELECT 1 FROM browser_profile_states WHERE profile_ref = %s",
                    (profile_ref,),
                )
                return cursor.fetchone() is not None
    except Exception as exc:
        raise RuntimeError(f"browser session database check failed ({type(exc).__name__})") from None


def restore_storage_state(context, state: dict[str, Any]) -> None:
    state = _normalise_state(state)
    cookies = state["cookies"]
    if cookies:
        context.add_cookies(cookies)
    origins = state["origins"]
    if not origins:
        return
    origins_json = json.dumps(origins, ensure_ascii=True, separators=(",", ":"))
    origins_json = origins_json.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    script = f"""
(() => {{
  const originState = {origins_json};
  const marker = {_RESTORE_MARKER!r};
  try {{
    if (localStorage.getItem(marker) === "1") return;
    const saved = originState.find((item) => item.origin === window.location.origin);
    if (saved && Array.isArray(saved.localStorage)) {{
      for (const entry of saved.localStorage) {{
        if (entry && typeof entry.name === "string") {{
          localStorage.setItem(entry.name, String(entry.value ?? ""));
        }}
      }}
    }}
    localStorage.setItem(marker, "1");
  }} catch (_) {{}}
}})();
"""
    context.add_init_script(script=script)
