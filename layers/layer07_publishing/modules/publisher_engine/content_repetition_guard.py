"""Persistent per-account content/template repetition protection."""
from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import tempfile
import time
from dataclasses import dataclass
from typing import Optional


_DEFAULT_DB = os.path.join(tempfile.gettempdir(), "ucos_content_repetition.sqlite3")
_RESERVATION_TTL_SECONDS = 1800


@dataclass(frozen=True)
class RepetitionDecision:
    allowed: bool
    reason: str = ""
    content_fingerprint: str = ""
    template_fingerprint: str = ""
    reservation_id: Optional[int] = None


class ContentRepetitionGuard:
    """Reject exact content and repeated templates within one account target."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or os.environ.get("UCOS_CONTENT_HISTORY_DB") or _DEFAULT_DB
        parent = os.path.dirname(os.path.abspath(self.db_path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=5)
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def _init_db(self) -> None:
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS content_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    content_fingerprint TEXT NOT NULL,
                    template_fingerprint TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('reserved','published')),
                    post_id TEXT,
                    created_at REAL NOT NULL,
                    UNIQUE(account_id, content_fingerprint),
                    UNIQUE(account_id, template_fingerprint)
                )"""
            )
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_content_history_account ON content_history(account_id)"
            )

    def _clear_stale_reservations(self, db: sqlite3.Connection) -> None:
        db.execute(
            "DELETE FROM content_history WHERE status='reserved' AND created_at < ?",
            (time.time() - _RESERVATION_TTL_SECONDS,),
        )

    @staticmethod
    def _normalize_content(content: str) -> str:
        value = content.lower().strip()
        value = re.sub(r"https?://\S+|www\.\S+", " <url> ", value)
        value = re.sub(r"\b\d+(?:[.,]\d+)*%?\b", " <num> ", value)
        value = re.sub(r"[^\w\s<>!?.,:;'-]", " ", value)
        return re.sub(r"\s+", " ", value).strip()

    @classmethod
    def fingerprints(cls, content: str, explicit_template_id: Optional[str] = None) -> tuple[str, str]:
        normalized = cls._normalize_content(content)
        content_fp = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\n", content) if p.strip()]
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", normalized) if s.strip()]
        sentence_lengths = [min(len(re.findall(r"\b\w+\b", sentence)), 99) // 3 for sentence in sentences]
        paragraph_lengths = [min(len(re.findall(r"\b\w+\b", paragraph)), 999) // 5 for paragraph in paragraphs]
        markers = "".join(
            marker for marker, present in (
                ("Q", "?" in content),
                ("E", "!" in content),
                ("B", bool(re.search(r"(?:^|\n)\s*[-*•]\s+", content))),
                ("H", bool(re.search(r"(?:^|\n)\s*#+\s+", content))),
            ) if present
        )
        template_basis = explicit_template_id or "|".join(
            (
                f"p={len(paragraphs)}",
                f"s={len(sentences)}",
                f"sl={','.join(map(str, sentence_lengths))}",
                f"pl={','.join(map(str, paragraph_lengths))}",
                f"m={markers}",
            )
        )
        template_fp = hashlib.sha256(template_basis.encode("utf-8")).hexdigest()
        return content_fp, template_fp

    def reserve(
        self,
        *,
        account_id: str,
        platform: str,
        content: str,
        template_id: Optional[str] = None,
    ) -> RepetitionDecision:
        account = account_id.strip()
        if not account:
            raise ValueError("account_id is required for repetition protection")
        if not content.strip():
            raise ValueError("content is required for repetition protection")
        content_fp, template_fp = self.fingerprints(content, template_id)
        try:
            with self._connect() as db:
                self._clear_stale_reservations(db)
                exact = db.execute(
                    "SELECT 1 FROM content_history WHERE account_id=? AND content_fingerprint=? LIMIT 1",
                    (account, content_fp),
                ).fetchone()
                if exact:
                    return RepetitionDecision(False, "exact_content_repeat", content_fp, template_fp)
                template = db.execute(
                    "SELECT 1 FROM content_history WHERE account_id=? AND template_fingerprint=? LIMIT 1",
                    (account, template_fp),
                ).fetchone()
                if template:
                    return RepetitionDecision(False, "template_repeat", content_fp, template_fp)
                cursor = db.execute(
                    """INSERT INTO content_history
                       (account_id, platform, content_fingerprint, template_fingerprint, status, created_at)
                       VALUES (?, ?, ?, ?, 'reserved', ?)""",
                    (account, platform.strip().lower(), content_fp, template_fp, time.time()),
                )
                return RepetitionDecision(True, "reserved", content_fp, template_fp, cursor.lastrowid)
        except sqlite3.IntegrityError:
            return RepetitionDecision(False, "concurrent_repetition_detected", content_fp, template_fp)

    def finalize(self, reservation_id: int, post_id: Optional[str]) -> None:
        with self._connect() as db:
            updated = db.execute(
                "UPDATE content_history SET status='published', post_id=? WHERE id=? AND status='reserved'",
                (post_id, reservation_id),
            ).rowcount
            if updated != 1:
                raise RuntimeError(f"Invalid repetition reservation: {reservation_id}")

    def release(self, reservation_id: int) -> None:
        with self._connect() as db:
            db.execute(
                "DELETE FROM content_history WHERE id=? AND status='reserved'",
                (reservation_id,),
            )
