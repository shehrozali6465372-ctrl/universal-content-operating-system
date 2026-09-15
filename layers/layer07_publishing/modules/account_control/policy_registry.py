"""Versioned, data-driven platform policy registry.

Policies are configuration, not invented platform claims. A policy may be supplied
by deployment configuration or persisted locally with an explicit source/version.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PlatformPolicy:
    platform: str
    version: str
    source: str = ""
    fetched_at: float = 0.0
    constraints: Dict[str, Any] = field(default_factory=dict)
    content_gate: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.platform.strip():
            raise ValueError("platform is required")
        if not self.version.strip():
            raise ValueError("policy version is required")


class PolicyRegistry:
    """Persistent policy snapshots keyed by platform and version."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = Path(db_path or os.getenv("UCOS_POLICY_DB", "./data/policies/registry.sqlite3"))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS policies(
                platform TEXT NOT NULL, version TEXT NOT NULL, source TEXT NOT NULL,
                fetched_at REAL NOT NULL, constraints_json TEXT NOT NULL,
                content_gate_json TEXT NOT NULL, PRIMARY KEY(platform, version))""")

    def register(self, policy: PlatformPolicy) -> None:
        policy.validate()
        fetched = policy.fetched_at or time.time()
        with sqlite3.connect(self.db_path) as db:
            db.execute("""INSERT OR REPLACE INTO policies
                (platform,version,source,fetched_at,constraints_json,content_gate_json)
                VALUES(?,?,?,?,?,?)""", (
                policy.platform.strip().lower(), policy.version, policy.source, fetched,
                json.dumps(policy.constraints, sort_keys=True),
                json.dumps(policy.content_gate, sort_keys=True)))

    def get(self, platform: str, version: Optional[str] = None) -> Optional[PlatformPolicy]:
        platform = platform.strip().lower()
        with sqlite3.connect(self.db_path) as db:
            if version:
                row = db.execute("SELECT platform,version,source,fetched_at,constraints_json,content_gate_json FROM policies WHERE platform=? AND version=?", (platform, version)).fetchone()
            else:
                row = db.execute("SELECT platform,version,source,fetched_at,constraints_json,content_gate_json FROM policies WHERE platform=? ORDER BY fetched_at DESC LIMIT 1", (platform,)).fetchone()
        if not row:
            return None
        return PlatformPolicy(row[0], row[1], row[2], row[3], json.loads(row[4]), json.loads(row[5]))

    def list(self, platform: Optional[str] = None) -> List[PlatformPolicy]:
        with sqlite3.connect(self.db_path) as db:
            if platform:
                rows = db.execute("SELECT platform,version,source,fetched_at,constraints_json,content_gate_json FROM policies WHERE platform=? ORDER BY fetched_at DESC", (platform.strip().lower(),)).fetchall()
            else:
                rows = db.execute("SELECT platform,version,source,fetched_at,constraints_json,content_gate_json FROM policies ORDER BY platform,fetched_at DESC").fetchall()
        return [PlatformPolicy(r[0], r[1], r[2], r[3], json.loads(r[4]), json.loads(r[5])) for r in rows]

    def export(self, platform: str) -> Dict[str, Any]:
        policy = self.get(platform)
        return asdict(policy) if policy else {}
