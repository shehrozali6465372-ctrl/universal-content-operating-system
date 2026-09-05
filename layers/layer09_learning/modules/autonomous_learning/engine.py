"""Real, context-isolated continuous learning engine.

The engine learns only from persisted real observations supplied by callers. It
never fabricates outcomes, marks unverified actions as successful, or silently
shares observations between contexts.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .model import OnlineRegressor
from .scope import LearningScope


@dataclass(frozen=True)
class LearningEvent:
    event_id: str
    scope: LearningScope
    features: Tuple[float, ...]
    reward: Optional[float]
    label: Optional[float]
    created_at: str
    source: str


@dataclass(frozen=True)
class Prediction:
    scope_key: str
    model_version: str
    value: float
    trained_on: int
    confidence: Optional[float]


class AutonomousLearningEngine:
    """Persistent ML engine with hard scope isolation and evidence gates."""

    def __init__(self, db_path: str | Path = "data/layer09_learning.db") -> None:
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._models: Dict[str, OnlineRegressor] = {}
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS learning_events (
                    event_id TEXT PRIMARY KEY,
                    scope_key TEXT NOT NULL,
                    platform_id TEXT NOT NULL,
                    niche_id TEXT NOT NULL,
                    audience_id TEXT NOT NULL,
                    country TEXT NOT NULL,
                    language TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    experiment_id TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    features_json TEXT NOT NULL,
                    reward REAL,
                    label REAL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_events_scope ON learning_events(scope_key);
                CREATE INDEX IF NOT EXISTS idx_events_experiment ON learning_events(experiment_id);
                CREATE TABLE IF NOT EXISTS model_registry (
                    scope_key TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    sample_count INTEGER NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(scope_key, model_version)
                );
                """
            )

    def record_outcome(
        self,
        scope: LearningScope,
        features: Sequence[float],
        reward: float,
        *,
        source: str,
        experiment_id: str = "",
        model_version: str = "untrained",
        label: Optional[float] = None,
        event_id: Optional[str] = None,
    ) -> LearningEvent:
        """Persist one real observation and its measured outcome.

        ``reward`` must come from an actual external outcome. The engine does
        not generate defaults or infer success from an action being completed.
        """
        if not source.strip():
            raise ValueError("source is required; synthetic/anonymous outcomes are rejected")
        values = tuple(float(x) for x in features)
        if not values:
            raise ValueError("at least one real feature is required")
        if not all(x == x and abs(x) != float("inf") for x in values):
            raise ValueError("features must be finite")
        reward = float(reward)
        if reward != reward or abs(reward) == float("inf"):
            raise ValueError("reward must be finite")
        eid = event_id or hashlib.sha256(
            (scope.key + json.dumps(values) + str(reward) + source + experiment_id).encode()
        ).hexdigest()
        event = LearningEvent(
            event_id=eid,
            scope=scope,
            features=values,
            reward=reward,
            label=None if label is None else float(label),
            created_at=datetime.now(timezone.utc).isoformat(),
            source=source,
        )
        with self._connect() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO learning_events
                (event_id, scope_key, platform_id, niche_id, audience_id, country,
                 language, content_type, experiment_id, model_version, features_json,
                 reward, label, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    event.event_id, scope.key, scope.platform_id, scope.niche_id,
                    scope.audience_id, scope.country, scope.language,
                    scope.content_type, experiment_id, model_version,
                    json.dumps(values), reward, event.label, source, event.created_at,
                ),
            )
        return event

    def train(self, scope: LearningScope, *, min_samples: int = 20) -> Dict[str, Any]:
        """Train a real supervised model from persisted outcomes for one scope.

        No model is produced when evidence is insufficient. The target is the
        measured reward recorded by ``record_outcome``.
        """
        rows = self._rows(scope)
        if len(rows) < min_samples:
            return {"status": "insufficient_data", "scope_key": scope.key, "samples": len(rows)}
        X = [json.loads(row["features_json"]) for row in rows]
        y = [float(row["reward"]) for row in rows]
        model = OnlineRegressor()
        report = model.fit(X, y)
        version = model.version
        self._models[scope.key] = model
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO model_registry VALUES (?, ?, ?, ?, ?, ?, ?)",
                (scope.key, version, len(rows), report["metric_name"], report["metric_value"], "candidate", datetime.now(timezone.utc).isoformat()),
            )
        return {"status": "trained", "scope_key": scope.key, "samples": len(rows), "model_version": version, **report}

    def predict(self, scope: LearningScope, features: Sequence[float]) -> Prediction:
        model = self._models.get(scope.key)
        if model is None:
            raise RuntimeError(f"no trained model for scope {scope.key}; refusing unverified prediction")
        value = model.predict([list(map(float, features))])[0]
        return Prediction(scope.key, model.version, value, model.sample_count, model.confidence)

    def _rows(self, scope: LearningScope) -> List[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM learning_events WHERE scope_key = ? AND reward IS NOT NULL ORDER BY created_at",
                (scope.key,),
            ).fetchall()

    def count(self, scope: LearningScope) -> int:
        with self._connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM learning_events WHERE scope_key = ?", (scope.key,)).fetchone()[0])

    def audit_scope_isolation(self, scopes: Iterable[LearningScope]) -> Dict[str, Any]:
        keys = [scope.key for scope in scopes]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate learning scopes supplied")
        counts = {key: self._count_key(key) for key in keys}
        return {"isolated": True, "scopes": counts}

    def _count_key(self, key: str) -> int:
        with self._connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM learning_events WHERE scope_key = ?", (key,)).fetchone()[0])
