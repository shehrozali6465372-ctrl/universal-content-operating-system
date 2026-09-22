"""Authoritative lineage/event contract for source-to-revenue tracking."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from layers.layer13_persistence.modules.postgresql.connection.pool import ConnectionPool

STAGES = (
    "source", "niche", "keyword", "content", "asset", "platform", "account",
    "publish", "click", "conversion", "revenue",
)
_PARENT = {stage: STAGES[index - 1] for index, stage in enumerate(STAGES) if index}


@dataclass(frozen=True)
class LineageEvent:
    event_id: str
    lineage_id: str
    stage: str
    entity_id: str
    parent_event_id: Optional[str]
    source: str
    source_id: str
    provider: str
    status: str
    confidence: Optional[float]
    payload_hash: str
    error_code: Optional[str]
    observed_at: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LineageStore:
    """Persistent lineage ledger using UCOS PostgreSQL in production."""

    def __init__(self, pool: Optional[ConnectionPool] = None, db_path: Optional[str] = None) -> None:
        self._pool = None if db_path else (pool or ConnectionPool())
        self._sqlite = sqlite3.connect(db_path, check_same_thread=False) if db_path else None
        if self._sqlite:
            self._sqlite.row_factory = sqlite3.Row
        if self._pool:
            self._pool.initialize()
        self._init_schema()

    def _execute(self, sql: str, params: tuple = ()) -> int:
        if self._sqlite:
            cur = self._sqlite.execute(sql.replace("%s", "?"), params)
            self._sqlite.commit()
            return cur.rowcount
        return self._pool.execute(sql, params)

    def _query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        if self._sqlite:
            return [dict(r) for r in self._sqlite.execute(sql.replace("%s", "?"), params).fetchall()]
        return self._pool.query(sql, params)

    def _init_schema(self) -> None:
        self._execute("""CREATE TABLE IF NOT EXISTS ucos_lineage_events (
            event_id TEXT PRIMARY KEY,
            lineage_id TEXT NOT NULL,
            stage TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            parent_event_id TEXT,
            source TEXT NOT NULL,
            source_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            status TEXT NOT NULL,
            confidence REAL,
            payload_hash TEXT NOT NULL,
            error_code TEXT,
            observed_at REAL NOT NULL
        )""")
        self._execute("CREATE INDEX IF NOT EXISTS idx_uelos_lineage_stage ON ucos_lineage_events(lineage_id, stage)")
        self._execute("CREATE INDEX IF NOT EXISTS idx_uelos_source ON ucos_lineage_events(source, source_id)")

    @staticmethod
    def _payload_hash(payload: Any) -> str:
        normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def _event_id(lineage_id: str, stage: str, entity_id: str, payload_hash: str) -> str:
        raw = f"{lineage_id}|{stage}|{entity_id}|{payload_hash}".encode("utf-8")
        return str(uuid.uuid5(uuid.NAMESPACE_URL, hashlib.sha256(raw).hexdigest()))

    def record(
        self, *, lineage_id: str, stage: str, entity_id: str, source: str,
        source_id: str, provider: str, status: str, payload: Any = None,
        parent_event_id: Optional[str] = None, confidence: Optional[float] = None,
        error_code: Optional[str] = None, observed_at: Optional[float] = None,
    ) -> LineageEvent:
        if stage not in STAGES:
            raise ValueError(f"unsupported lineage stage: {stage}")
        if status not in {"observed", "pending", "failed"}:
            raise ValueError(f"unsupported lineage status: {status}")
        if not lineage_id.strip() or not entity_id.strip() or not source.strip() or not source_id.strip():
            raise ValueError("lineage_id, entity_id, source and source_id are required")
        if confidence is not None and not 0.0 <= float(confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        expected_parent_stage = _PARENT.get(stage)
        if expected_parent_stage and not parent_event_id:
            prior = self._query(
                "SELECT event_id FROM ucos_lineage_events WHERE lineage_id=%s AND stage=%s ORDER BY observed_at DESC LIMIT 1",
                (lineage_id, expected_parent_stage),
            )
            parent_event_id = prior[0]["event_id"] if prior else None
        if expected_parent_stage and not parent_event_id:
            raise ValueError(f"stage {stage} requires a recorded parent stage {expected_parent_stage}")
        if parent_event_id:
            parent = self._query(
                "SELECT stage,lineage_id FROM ucos_lineage_events WHERE event_id=%s",
                (parent_event_id,),
            )
            if not parent or parent[0]["lineage_id"] != lineage_id or parent[0]["stage"] != expected_parent_stage:
                raise ValueError("parent_event_id does not match lineage/stage contract")
        payload_hash = self._payload_hash(payload)
        event_id = self._event_id(lineage_id, stage, entity_id, payload_hash)
        event = LineageEvent(
            event_id=event_id, lineage_id=lineage_id, stage=stage, entity_id=entity_id,
            parent_event_id=parent_event_id, source=source, source_id=source_id,
            provider=provider, status=status, confidence=confidence, payload_hash=payload_hash,
            error_code=error_code, observed_at=float(observed_at or time.time()),
        )
        self._execute(
            """INSERT INTO ucos_lineage_events
            (event_id,lineage_id,stage,entity_id,parent_event_id,source,source_id,provider,status,confidence,payload_hash,error_code,observed_at)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT(event_id) DO NOTHING""",
            (event.event_id,event.lineage_id,event.stage,event.entity_id,event.parent_event_id,event.source,
             event.source_id,event.provider,event.status,event.confidence,event.payload_hash,event.error_code,event.observed_at),
        )
        rows = self._query("SELECT * FROM ucos_lineage_events WHERE event_id=%s", (event_id,))
        return LineageEvent(**rows[0])

    def get_lineage(self, lineage_id: str) -> List[LineageEvent]:
        rows = self._query(
            "SELECT * FROM ucos_lineage_events WHERE lineage_id=%s ORDER BY observed_at,event_id",
            (lineage_id,),
        )
        return [LineageEvent(**row) for row in rows]

    def close(self) -> None:
        if self._sqlite:
            self._sqlite.close()
        elif self._pool:
            self._pool.close()
