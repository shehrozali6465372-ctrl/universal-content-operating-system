"""Persistent content/template repetition guard for real publishing.

The guard operates before media upload/publishing. It stores fingerprints in a
small SQLite database so a process restart does not reset repetition history.
The scope is an account target, not merely a platform, when ``account_id`` is
provided in PublishRequest.metadata.

No synthetic analytics or publish records are created here: a history row is
created only after the publisher reports a successful post.
"""
from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import tempfile
from dataclasses import dataclass
from typing import Optional


_DEFAULT_DB = os.path.join(tempfile.gettempdir(), "ucos_content_repetition.sqlite3")


@dataclass(frozen=True)
class RepetitionDecision:
    allowed: bool
    reason: str = ""
    content_fingerprint: str = ""
    template_fingerprint: str = ""


class ContentRepetitionGuard:
    """Reject exact content or repeated structural templates per account."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or os.environ.get("UCOS_CONTENT_HISTORY_DB") or _DEFAULT_DB
        parent = os.path.dirname(os.path.abspath(self.db_path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
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
                    created_at REAL NOT NULL DEFAULT (unixepoch()),
                    UNIQUE(account_id, content_fingerprint),
                    UNIQUE(account_id, template_fingerprint)
                )"""
            )
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_content_history_account ON content_history(account_id)"
            )

    @staticmethod
    def _normalize_content(content: str) -> str:
        value = content.lower().strip()
        value = re.sub(r"https?://\\S+|www\\.\\S+", " <url> ", value)
        value = re.sub(r"\\b\\d+(?:[.,]\\d+)*%?\\b", " <num> ", value)
        value = re.sub(r"[^\\w\\s<>!?.,:;'-]", " ", value)
        return re.sub(r"\\s+", " ", value).strip()

    @classmethod
    def fingerprints(cls, content: str, explicit_template_id: Optional[str] = None) -> tuple[str, str]:
        normalized = cls._normalize_content(content)
        content_fp = hashlib.sha256(normalized.encode("utf-8")).hexdigest()

        paragraphs = [p.strip() for p in re.split(r"\\n\\s*\\n|\\n", content) if p.strip()]
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\\s+", normalized) if s.strip()]
        lengths = [min(len(re.findall(r"\\b\\w+\\b", sentence)), 99) for sentence in sentences]
        paragraph_shape = [min(len(re.findall(r"\\b\\w+\\b", paragraph)), 999) // 5 for paragraph in paragraphs]
        markers = "".join(
            "Q" if "?" in content else "",
        ) + "".join(
            marker for marker, present in (
                ("E", "!" in content),
                ("B", bool(re.search(r"(?:^|\\n)\\s*[-*•]\\s+", content))),
                ("H", bool(re.search(r"(?:^|\\n)\\s*#+\\s+", content))),
            ) if present
        )
        hook = " ".join(normalized.split()[:12])
        template_basis = explicit_template_id or "|".join(
            [
                f"p={len(paragraphs)}",
                f"s={len(sentences)}",
                f"sl={','.join(map(str, lengths))}",
                f"pl={','.join(map(str, paragraph_shape))}",
                f"m={markers}",
                f"h={hook}",
            ]
        )
        template_fp = hashlib.sha256(template_basis.encode("utf-8")).hexdigest()
        return content_fp, template_fp

    def check(
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
        with self._connect() as db:
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
        return RepetitionDecision(True, "unique", content_fp, template_fp)

    def record_success(
        self,
        *,
        account_id: str,
        platform: str,
        content: str,
        template_id: Optional[str] = None,
    ) -> RepetitionDecision:
        decision = self.check(
            account_id=account_id,
            platform=platform,
            content=content,
            template_id=template_id,
        )
        if not decision.allowed:
            return decision
        with self._connect() as db:
            db.execute(
                """INSERT INTO content_history
                   (account_id, platform, content_fingerprint, template_fingerprint)
                   VALUES (?, ?, ?, ?)""",
                (account_id.strip(), platform.strip().lower(), decision.content_fingerprint, decision.template_fingerprint),
            )
        return decision
