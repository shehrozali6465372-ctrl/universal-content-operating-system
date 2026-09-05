"""Persistent, scope-isolated experimentation with measured statistics."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import math
import sqlite3
from typing import Optional

from .scope import LearningScope


@dataclass(frozen=True)
class ExperimentResult:
    experiment_id: str
    scope_key: str
    status: str
    control_n: int
    treatment_n: int
    control_rate: Optional[float]
    treatment_rate: Optional[float]
    uplift: Optional[float]
    p_value: Optional[float]
    ci_low: Optional[float]
    ci_high: Optional[float]
    winner: Optional[str]


class ScopedExperiment:
    """Randomized experiment state keyed by the complete LearningScope."""

    def __init__(self, db_path: str = "data/layer09_learning.db") -> None:
        self.db_path = db_path
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS experiments (
                    experiment_id TEXT PRIMARY KEY, scope_key TEXT NOT NULL,
                    control_policy TEXT NOT NULL, treatment_policy TEXT NOT NULL,
                    min_samples_per_arm INTEGER NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS experiment_assignments (
                    experiment_id TEXT NOT NULL, subject_id TEXT NOT NULL,
                    scope_key TEXT NOT NULL, arm TEXT NOT NULL CHECK(arm IN ('control','treatment')),
                    assigned_at TEXT NOT NULL, PRIMARY KEY(experiment_id, subject_id)
                );
                CREATE TABLE IF NOT EXISTS experiment_outcomes (
                    experiment_id TEXT NOT NULL, subject_id TEXT NOT NULL,
                    scope_key TEXT NOT NULL, success INTEGER NOT NULL CHECK(success IN (0,1)),
                    observed_at TEXT NOT NULL, PRIMARY KEY(experiment_id, subject_id)
                );
                CREATE INDEX IF NOT EXISTS idx_experiment_scope ON experiments(scope_key);
                CREATE INDEX IF NOT EXISTS idx_assignment_scope ON experiment_assignments(scope_key);
                CREATE INDEX IF NOT EXISTS idx_outcome_scope ON experiment_outcomes(scope_key);
            """)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create(self, scope: LearningScope, experiment_id: str, *, control_policy: str, treatment_policy: str, min_samples_per_arm: int = 100) -> None:
        if not experiment_id.strip() or not control_policy.strip() or not treatment_policy.strip():
            raise ValueError("experiment_id and both policies are required")
        if min_samples_per_arm < 2:
            raise ValueError("min_samples_per_arm must be >= 2")
        with self._connect() as conn:
            conn.execute("INSERT INTO experiments VALUES (?,?,?,?,?,?)",
                         (experiment_id, scope.key, control_policy, treatment_policy, min_samples_per_arm,
                          datetime.now(timezone.utc).isoformat()))

    def assign(self, scope: LearningScope, experiment_id: str, subject_id: str) -> str:
        if not subject_id.strip():
            raise ValueError("subject_id is required")
        with self._connect() as conn:
            exp = conn.execute("SELECT * FROM experiments WHERE experiment_id=? AND scope_key=?", (experiment_id, scope.key)).fetchone()
            if exp is None:
                raise KeyError("experiment does not exist in the exact learning scope")
            row = conn.execute("SELECT arm FROM experiment_assignments WHERE experiment_id=? AND subject_id=? AND scope_key=?",
                               (experiment_id, subject_id, scope.key)).fetchone()
            if row:
                return str(row["arm"])
            digest = hashlib.sha256(f"{experiment_id}|{scope.key}|{subject_id}".encode()).digest()
            arm = "treatment" if int.from_bytes(digest[:8], "big") % 2 else "control"
            conn.execute("INSERT INTO experiment_assignments VALUES (?,?,?,?,?)",
                         (experiment_id, subject_id, scope.key, arm, datetime.now(timezone.utc).isoformat()))
            return arm

    def record_outcome(self, scope: LearningScope, experiment_id: str, subject_id: str, success: bool) -> None:
        with self._connect() as conn:
            assignment = conn.execute("""SELECT a.arm FROM experiment_assignments a
                JOIN experiments e ON e.experiment_id=a.experiment_id
                WHERE a.experiment_id=? AND a.subject_id=? AND a.scope_key=? AND e.scope_key=?""",
                                      (experiment_id, subject_id, scope.key, scope.key)).fetchone()
            if assignment is None:
                raise ValueError("cannot record outcome before an exact-scope assignment")
            conn.execute("INSERT INTO experiment_outcomes VALUES (?,?,?,?,?)",
                         (experiment_id, subject_id, scope.key, int(bool(success)), datetime.now(timezone.utc).isoformat()))

    def evaluate(self, scope: LearningScope, experiment_id: str) -> ExperimentResult:
        with self._connect() as conn:
            exp = conn.execute("SELECT * FROM experiments WHERE experiment_id=? AND scope_key=?", (experiment_id, scope.key)).fetchone()
            if exp is None:
                raise KeyError("experiment does not exist in the exact learning scope")
            rows = conn.execute("""SELECT a.arm,o.success FROM experiment_assignments a
                JOIN experiment_outcomes o ON a.experiment_id=o.experiment_id AND a.subject_id=o.subject_id AND a.scope_key=o.scope_key
                WHERE a.experiment_id=? AND a.scope_key=?""", (experiment_id, scope.key)).fetchall()
        control = [int(r["success"]) for r in rows if r["arm"] == "control"]
        treatment = [int(r["success"]) for r in rows if r["arm"] == "treatment"]
        min_n = int(exp["min_samples_per_arm"])
        if min(len(control), len(treatment)) < min_n:
            return ExperimentResult(experiment_id, scope.key, "insufficient_evidence", len(control), len(treatment), None, None, None, None, None, None, None)
        p0, p1 = sum(control)/len(control), sum(treatment)/len(treatment)
        uplift = p1 - p0
        se = math.sqrt(max(1e-15, p0*(1-p0)/len(control) + p1*(1-p1)/len(treatment)))
        z = uplift / se
        p_value = math.erfc(abs(z) / math.sqrt(2.0))
        margin = 1.96 * se
        low, high = uplift-margin, uplift+margin
        winner, status = None, "inconclusive"
        if p_value < 0.05 and low > 0:
            winner, status = "treatment", "verified_treatment"
        elif p_value < 0.05 and high < 0:
            winner, status = "control", "verified_control"
        return ExperimentResult(experiment_id, scope.key, status, len(control), len(treatment), p0, p1, uplift, p_value, low, high, winner)
