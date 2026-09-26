"""AtoZ Product Hub integration adapter for UCOS Layer 23.

The repositories remain separate. This adapter exposes only the documented
AIOS.Job.Request transport surface and calls real Layer 23 operations.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from layers.layer23_website_manager import get_website
from layers.layer23_website_manager.pinterest_pin_manager.pinterest_pin_manager import (
    get_pin_manager,
)

_LOGGER = logging.getLogger(__name__)
_INBOX_DB = Path(os.environ.get("UCOS_JOB_INBOX_DB", "data/job_inbox.sqlite3"))
_LEASE_SECONDS = 900.0

SUPPORTED_JOB_TYPES = {"content", "seo_metadata", "pinterest_assets", "analytics_insights"}


def _connect() -> sqlite3.Connection:
    db = sqlite3.connect(_INBOX_DB, timeout=30.0)
    db.execute("PRAGMA busy_timeout=30000")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=FULL")
    return db


def _init_inbox() -> None:
    _INBOX_DB.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS job_inbox (
                request_id TEXT PRIMARY KEY,
                payload_hash TEXT NOT NULL,
                state TEXT NOT NULL,
                response_json TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                lease_token TEXT,
                lease_expires_at REAL
            )"""
        )
        columns = {row[1] for row in db.execute("PRAGMA table_info(job_inbox)")}
        if "lease_token" not in columns:
            db.execute("ALTER TABLE job_inbox ADD COLUMN lease_token TEXT")
        if "lease_expires_at" not in columns:
            db.execute("ALTER TABLE job_inbox ADD COLUMN lease_expires_at REAL")
        db.execute("CREATE INDEX IF NOT EXISTS idx_job_inbox_state ON job_inbox(state)")
        db.commit()


def _payload_hash(data: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _claim_request(request_id: str, payload_hash: str) -> tuple[dict[str, Any] | None, str]:
    """Atomically claim a request and return (cached_response, lease_token)."""
    _init_inbox()
    now = time.time()
    lease_token = str(uuid.uuid4())

    with _connect() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute(
            """SELECT payload_hash, state, response_json, lease_token, lease_expires_at
               FROM job_inbox WHERE request_id=?""",
            (request_id,),
        ).fetchone()

        if row:
            stored_hash, state, response_json, current_token, lease_expires_at = row
            if stored_hash != payload_hash:
                db.rollback()
                raise ValueError("request_id replay conflict: payload differs from original request")
            if response_json:
                db.commit()
                return json.loads(response_json), current_token or ""
            if state == "processing":
                if lease_expires_at is not None and lease_expires_at > now:
                    db.rollback()
                    raise RuntimeError("request_id requires reconciliation: already processing")
                db.execute(
                    """UPDATE job_inbox
                       SET state='processing', response_json=NULL,
                           lease_token=?, lease_expires_at=?, updated_at=CURRENT_TIMESTAMP
                       WHERE request_id=?""",
                    (lease_token, now + _LEASE_SECONDS, request_id),
                )
                db.commit()
                return None, lease_token
            db.rollback()
            raise RuntimeError("request_id has no terminal response")

        db.execute(
            """INSERT INTO job_inbox(
                   request_id, payload_hash, state, lease_token, lease_expires_at
               ) VALUES (?, ?, 'processing', ?, ?)""",
            (request_id, payload_hash, lease_token, now + _LEASE_SECONDS),
        )
        db.commit()
    return None, lease_token


def _finish_request(
    request_id: str,
    lease_token: str,
    response: dict[str, Any],
    state: str = "succeeded",
) -> bool:
    """Complete a request only if this worker still owns its lease."""
    with _connect() as db:
        cursor = db.execute(
            """UPDATE job_inbox
               SET state=?, response_json=?, lease_expires_at=NULL,
                   updated_at=CURRENT_TIMESTAMP
               WHERE request_id=? AND lease_token=? AND state='processing'""",
            (state, json.dumps(response, sort_keys=True, default=str), request_id, lease_token),
        )
        db.commit()
        return cursor.rowcount == 1


def _uuid(value: Any, field: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValueError(f"{field} must be a valid UUID") from exc


def dispatch_job(data: dict[str, Any]) -> dict[str, Any]:
    """Dispatch an AIOS job into Layer 23 using real data only."""
    if not isinstance(data, dict):
        raise ValueError("job request must be an object")

    request_id = _uuid(data.get("request_id"), "request_id")
    niche_id = _uuid(data.get("niche_id"), "niche_id")
    job_type = str(data.get("job_type") or "").strip()
    if job_type not in SUPPORTED_JOB_TYPES:
        raise ValueError(f"unsupported job_type: {job_type}")

    context = data.get("context")
    if not isinstance(context, dict):
        raise ValueError("context must be an object")
    domain = str(context.get("domain") or "").strip()
    site_name = str(context.get("site_name") or "").strip()
    if not domain or not site_name:
        raise ValueError("context.domain and context.site_name are required")

    cached, lease_token = _claim_request(request_id, _payload_hash(data))
    if cached is not None:
        return cached

    job_id = str(uuid.uuid4())
    try:
        site = get_website(domain=domain, site_name=site_name)
        publish = bool(context.get("publish"))

        if publish and job_type != "content":
            raise ValueError("publish is only valid for content jobs")

        if publish:
            account_id = str(context.get("account_id") or "").strip()
            if not account_id:
                raise ValueError("publishing requires context.account_id")
            from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
            account = AccountRegistry().get(account_id)
            if account is None or not account.enabled:
                raise ValueError("publishing account is not registered and enabled")

        if job_type == "content":
            title = str(context.get("title") or "").strip()
            body = str(context.get("content") or "").strip()
            if not title or not body:
                raise ValueError("content jobs require real context.title and context.content")
            if publish and not bool(context.get("publish_authorized")):
                raise ValueError("publishing requires explicit publish_authorized=true")
            article = site.create_article(
                title=title,
                content=body,
                category=str(context.get("category") or ""),
                tags=list(context.get("tags") or []),
                author=str(context.get("author") or "AtozProductHub"),
                featured_image=str(context.get("featured_image") or ""),
                meta_title=str(context.get("meta_title") or ""),
                meta_description=str(context.get("meta_description") or ""),
                status="published" if publish else "draft",
            )
            response = {
                "job_id": job_id, "request_id": request_id, "niche_id": niche_id,
                "state": "succeeded",
                "result_ref": f"layer23:article:{article.article_id}",
                "result": article.to_dict(),
            }
        elif job_type == "seo_metadata":
            article_id = str(context.get("article_id") or "").strip()
            if not article_id:
                raise ValueError("seo_metadata jobs require context.article_id")
            metadata = site.generate_article_seo(article_id)
            if metadata is None:
                raise LookupError(f"article not found: {article_id}")
            response = {
                "job_id": job_id, "request_id": request_id, "niche_id": niche_id,
                "state": "succeeded", "result_ref": f"layer23:seo:{article_id}",
                "result": metadata.to_dict(),
            }
        elif job_type == "pinterest_assets":
            title = str(context.get("title") or "").strip()
            website_url = str(context.get("website_url") or "").strip()
            account_id = str(context.get("account_id") or "").strip()
            board_id = str(context.get("board_id") or "").strip()
            image_path = str(context.get("image_path") or "").strip()
            if not title or not website_url or not account_id or not board_id or not image_path:
                raise ValueError(
                    "pinterest_assets jobs require title, website_url, account_id, board_id and image_path"
                )
            parsed = urlsplit(website_url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError("website_url must be a valid public HTTP(S) URL")
            asset_root = Path(os.environ.get("UCOS_ASSET_ROOT", "data/assets")).expanduser().resolve()
            candidate = Path(image_path).expanduser().resolve()
            if asset_root not in candidate.parents or not candidate.is_file():
                raise ValueError("image_path must reference an existing file under UCOS_ASSET_ROOT")
            pin = get_pin_manager().create_pin(
                pin_title=title, account_id=account_id, board_id=board_id,
                description=str(context.get("description") or ""), website_url=website_url,
                image_path=str(candidate), niche=str(context.get("niche") or ""),
                keywords=list(context.get("keywords") or []),
            )
            response = {
                "job_id": job_id, "request_id": request_id, "niche_id": niche_id,
                "state": "succeeded", "result_ref": f"layer23:pinterest-pin:{pin.pin_id}",
                "result": pin.to_dict(), "published": False,
            }
        elif job_type == "analytics_insights":
            response = {
                "job_id": job_id, "request_id": request_id, "niche_id": niche_id,
                "state": "succeeded", "result_ref": "layer23:website:status",
                "result": site.get_status(),
            }
        else:
            raise NotImplementedError(job_type)

        if not _finish_request(request_id, lease_token, response):
            raise RuntimeError("request lease was lost before completion")
        return response
    except Exception as exc:
        failure = {
            "job_id": job_id, "request_id": request_id, "niche_id": niche_id,
            "state": "failed", "error": f"{type(exc).__name__}: {exc}",
        }
        try:
            if not _finish_request(request_id, lease_token, failure, state="failed"):
                _LOGGER.error("AtoZ request lease lost while recording failure: request_id=%s", request_id)
        except Exception:
            _LOGGER.exception("AtoZ request failure could not be durably recorded: request_id=%s", request_id)
        raise
