"""Canonical L07 publication ledger backed by the L13 PostgreSQL source of truth.

The ledger owns publication semantics while provider-specific API behavior remains
inside the registered provider adapter.  Production callers must use this path;
the legacy SQLite repetition guard is intentionally not used by production.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional
from uuid import UUID, uuid4

from layers.layer13_persistence.modules.postgresql.manager import get_database


_UNRESOLVED = {
    "RESERVED",
    "INTENT_CREATED",
    "CALLING",
    "SUBMITTED",
    "OUTCOME_UNKNOWN",
    "RECONCILING",
    "VERIFYING",
    "PUBLISHED_NOT_PUBLIC",
    "VERIFICATION_UNKNOWN",
    "IDENTITY_MISMATCH",
    "VERIFICATION_FAILED",
}

_TERMINAL = {"FAILED_CONFIRMED", "VERIFIED_PUBLIC", "EXPIRED_UNVERIFIED"}

_ALLOWED_TRANSITIONS = {
    "RESERVED": {"INTENT_CREATED"},
    "INTENT_CREATED": {"CALLING", "FAILED_CONFIRMED"},
    "CALLING": {"FAILED_CONFIRMED", "OUTCOME_UNKNOWN", "SUBMITTED"},
    "SUBMITTED": {
        "VERIFYING",
        "PUBLISHED_NOT_PUBLIC",
        "VERIFIED_PUBLIC",
        "VERIFICATION_UNKNOWN",
        "IDENTITY_MISMATCH",
        "VERIFICATION_FAILED",
    },
    "OUTCOME_UNKNOWN": {"RECONCILING"},
    "RECONCILING": {
        "SUBMITTED",
        "VERIFYING",
        "PUBLISHED_NOT_PUBLIC",
        "VERIFIED_PUBLIC",
        "VERIFICATION_UNKNOWN",
        "EXPIRED_UNVERIFIED",
        "IDENTITY_MISMATCH",
        "VERIFICATION_FAILED",
        "FAILED_CONFIRMED",
    },
    "VERIFYING": {
        "VERIFIED_PUBLIC",
        "PUBLISHED_NOT_PUBLIC",
        "VERIFICATION_UNKNOWN",
        "IDENTITY_MISMATCH",
        "VERIFICATION_FAILED",
        "EXPIRED_UNVERIFIED",
    },
    "PUBLISHED_NOT_PUBLIC": {
        "VERIFYING",
        "VERIFIED_PUBLIC",
        "VERIFICATION_UNKNOWN",
        "EXPIRED_UNVERIFIED",
    },
    "VERIFICATION_UNKNOWN": {
        "RECONCILING",
        "VERIFYING",
        "VERIFIED_PUBLIC",
        "PUBLISHED_NOT_PUBLIC",
        "EXPIRED_UNVERIFIED",
    },
    "IDENTITY_MISMATCH": {"RECONCILING", "VERIFICATION_FAILED", "EXPIRED_UNVERIFIED"},
    "VERIFICATION_FAILED": {"RECONCILING", "EXPIRED_UNVERIFIED"},
    "EXPIRED_UNVERIFIED": set(),
    "FAILED_CONFIRMED": set(),
    "VERIFIED_PUBLIC": set(),
}


class PublicationConflictError(RuntimeError):
    """A logical publication conflicts with an existing durable reservation."""


class UnresolvedPublicationError(RuntimeError):
    """An account/platform has an unresolved publication that blocks reuse."""

    def __init__(self, state: str, intent_id: str, age_seconds: float) -> None:
        super().__init__(
            f"unresolved publication intent {intent_id} state={state} age={age_seconds:.1f}s"
        )
        self.state = state
        self.intent_id = intent_id
        self.age_seconds = age_seconds


@dataclass(frozen=True)
class LedgerReservation:
    intent_id: str
    publish_operation_id: str
    state: str
    account_id: str
    platform: str
    platform_account_id: str
    idempotency_key: str
    publish_marker: str
    reused: bool = False


@dataclass(frozen=True)
class LedgerAttempt:
    attempt_id: str
    intent_id: str
    attempt_number: int
    provider: str
    provider_idempotency_key: str


class PublicationLedger:
    """PostgreSQL-backed reservation, attempt and verification semantics."""

    def __init__(self, database: Any = None) -> None:
        self._database = database or get_database()
        pool = getattr(self._database, "_pool", None)
        available = bool(getattr(self._database, "_postgresql_available", False))
        if pool is None or not available:
            if os.environ.get("APP_ENV", "development").strip().lower() in {"production", "prod"}:
                raise RuntimeError("PublicationLedger requires canonical PostgreSQL in production")
            raise RuntimeError("PublicationLedger requires an initialized PostgreSQL database")

    @staticmethod
    def _uuid(value: str, field: str) -> UUID:
        raw = str(value or "").strip()
        if raw.startswith("req_"):
            raw = raw[4:]
        try:
            return UUID(raw)
        except (ValueError, AttributeError) as exc:
            raise ValueError(f"{field} must be a UUID") from exc

    @staticmethod
    def _now_iso() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _json(value: Any, default: Any) -> str:
        data = value if value is not None else default
        return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)

    @staticmethod
    def _content_hash(content: str) -> str:
        return hashlib.sha256((content or "").encode("utf-8")).hexdigest()

    @staticmethod
    def _template_hash(template_id: Any, content: str) -> Optional[str]:
        if template_id:
            return hashlib.sha256(str(template_id).encode("utf-8")).hexdigest()
        return None

    @staticmethod
    def _age_seconds(created_at: Any) -> float:
        if isinstance(created_at, datetime):
            value = created_at
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return max(0.0, (datetime.now(timezone.utc) - value).total_seconds())
        return 0.0

    @staticmethod
    def _audit_insert(cursor: Any, intent_id: UUID, event_type: str, payload: Dict[str, Any], idempotency_key: str) -> None:
        cursor.execute(
            """
            INSERT INTO outbox_events
              (outbox_id,event_type,aggregate_type,aggregate_id,idempotency_key,payload_hash,payload,status)
            VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb,'PENDING')
            ON CONFLICT (idempotency_key) DO NOTHING
            """,
            (
                str(uuid4()),
                event_type,
                "publish_intent",
                str(intent_id),
                idempotency_key,
                hashlib.sha256(PublicationLedger._json(payload, {}).encode("utf-8")).hexdigest(),
                PublicationLedger._json(payload, {}),
            ),
        )

    def reserve(self, request: Any) -> LedgerReservation:
        meta = dict(getattr(request, "metadata", {}) or {})
        production = os.environ.get("APP_ENV", "development").strip().lower() in {"production", "prod"}
        account_id = str(meta.get("account_id") or "").strip()
        platform_account_id = str(meta.get("platform_account_id") or "").strip()
        tenant_id = str(meta.get("tenant_id") or "").strip()
        platform = str(getattr(request, "platform", "") or "").strip().lower()
        idempotency_key = str(getattr(request, "idempotency_key", "") or "").strip()
        workflow_id = str(meta.get("workflow_id") or getattr(request, "request_id", "") or "")
        publish_operation_id = str(meta.get("publish_operation_id") or "").strip()
        if production and not tenant_id:
            raise ValueError("tenant_id is required for production publication")
        if production and not platform_account_id:
            raise ValueError("platform_account_id is required for production publication")
        if not account_id or not platform or not idempotency_key:
            raise ValueError("account_id, platform and idempotency_key are required")
        workflow_uuid = self._uuid(workflow_id, "workflow_id")
        operation_uuid = self._uuid(publish_operation_id, "publish_operation_id") if publish_operation_id else uuid4()
        content_hash = self._content_hash(getattr(request, "content", "") or "")
        template_hash = self._template_hash(meta.get("template_id"), getattr(request, "content", "") or "")
        publish_mode = str(meta.get("publish_mode") or "production").strip().lower()
        if publish_mode not in {"staging", "production"}:
            raise ValueError("publish_mode must be 'staging' or 'production'")
        requested_visibility = str(meta.get("requested_visibility") or meta.get("visibility") or "PUBLIC").strip()
        marker = str(meta.get("publish_marker") or f"ucos:{operation_uuid}")
        policy_snapshot = meta.get("policy_snapshot") or {
            "policy_version": meta.get("policy_version"),
            "platform": platform,
        }
        assets = meta.get("content_asset_refs")
        if assets is None:
            assets = [getattr(asset, "asset_id", "") or getattr(asset, "file_path", "") for asset in getattr(request, "media_assets", [])]
        if production and not str(meta.get("workspace_id") or "").strip():
            raise ValueError("workspace_id is required for production publication")
        if production and not str(meta.get("brand_id") or "").strip():
            raise ValueError("brand_id is required for production publication")
        with self._database._pool.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO workflow_runs
                  (workflow_id,tenant_id,workspace_id,brand_id,account_id,platform,status)
                VALUES (%s,%s,%s,%s,%s,%s,'RUNNING')
                ON CONFLICT (workflow_id) DO NOTHING
                """,
                (
                    workflow_uuid,
                    tenant_id,
                    str(meta.get("workspace_id") or "") or None,
                    str(meta.get("brand_id") or "") or None,
                    account_id,
                    platform,
                ),
            )
            cursor.execute(
                """
                SELECT tenant_id,workspace_id,brand_id,account_id,platform
                FROM workflow_runs
                WHERE workflow_id=%s
                FOR UPDATE
                """,
                (str(workflow_uuid),),
            )
            workflow_row = cursor.fetchone()
            if not workflow_row:
                raise RuntimeError("workflow run could not be established")
            expected_identity = (
                tenant_id,
                str(meta.get("workspace_id") or "") or None,
                str(meta.get("brand_id") or "") or None,
                account_id,
                platform,
            )
            if tuple(workflow_row) != expected_identity:
                raise PublicationConflictError(
                    "workflow identity does not match tenant/workspace/brand/account/platform"
                )
            cursor.execute(
                """
                SELECT intent_id,publish_operation_id,state,idempotency_key,content_hash,
                       template_hash,publish_marker,account_id,platform,platform_account_id,created_at
                FROM publish_intents
                WHERE account_id=%s AND platform=%s AND platform_account_id=%s
                  AND idempotency_key=%s
                FOR UPDATE
                """,
                (account_id, platform, platform_account_id, idempotency_key),
            )
            existing = cursor.fetchone()
            if existing:
                row = dict(zip([d[0] for d in cursor.description], existing))
                if row["content_hash"] != content_hash:
                    raise PublicationConflictError(
                        "idempotency key already exists with a different content hash"
                    )
                if row["template_hash"] and template_hash and row["template_hash"] != template_hash:
                    raise PublicationConflictError(
                        "idempotency key already exists with a different template"
                    )
                return LedgerReservation(
                    intent_id=str(row["intent_id"]),
                    publish_operation_id=str(row["publish_operation_id"]),
                    state=str(row["state"]),
                    account_id=str(row["account_id"]),
                    platform=str(row["platform"]),
                    platform_account_id=str(row["platform_account_id"]),
                    idempotency_key=str(row["idempotency_key"]),
                    publish_marker=str(row["publish_marker"] or ""),
                    reused=True,
                )
            cursor.execute(
                """
                SELECT intent_id,state,created_at
                FROM publish_intents
                WHERE account_id=%s AND platform=%s AND platform_account_id=%s
                  AND state = ANY(%s)
                ORDER BY created_at DESC
                FOR UPDATE
                """,
                (account_id, platform, platform_account_id, list(_UNRESOLVED)),
            )
            blocked = cursor.fetchone()
            if blocked:
                intent_id, state, created_at = blocked
                raise UnresolvedPublicationError(
                    str(state), str(intent_id), self._age_seconds(created_at)
                )
            intent_id = uuid4()
            cursor.execute(
                """
                INSERT INTO publish_intents
                  (intent_id,workflow_id,publish_operation_id,tenant_id,workspace_id,brand_id,
                   account_id,platform,platform_account_id,publish_mode,state,idempotency_key,
                   content_hash,template_hash,publish_marker,requested_visibility,
                   policy_snapshot,content_asset_refs,tracked_link_ref,reserved_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'RESERVED',%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s)
                """,
                (
                    intent_id,
                    workflow_uuid,
                    operation_uuid,
                    tenant_id,
                    str(meta.get("workspace_id") or "") or None,
                    str(meta.get("brand_id") or "") or None,
                    account_id,
                    platform,
                    platform_account_id,
                    publish_mode,
                    idempotency_key,
                    content_hash,
                    template_hash,
                    marker,
                    requested_visibility,
                    self._json(policy_snapshot, {}),
                    self._json(assets, []),
                    str(meta.get("tracked_link_ref") or "") or None,
                    self._now_iso(),
                ),
            )
            self._transition_locked(
                cursor,
                intent_id,
                "RESERVED",
                "INTENT_CREATED",
                idempotency_key,
                {"request_id": getattr(request, "request_id", ""), "workflow_id": str(workflow_uuid)},
            )
            return LedgerReservation(
                intent_id=str(intent_id),
                publish_operation_id=str(operation_uuid),
                state="INTENT_CREATED",
                account_id=account_id,
                platform=platform,
                platform_account_id=platform_account_id,
                idempotency_key=idempotency_key,
                publish_marker=marker,
            )

    def _transition_locked(
        self,
        cursor: Any,
        intent_id: UUID,
        prior_state: str,
        next_state: str,
        base_key: str,
        payload: Dict[str, Any],
    ) -> None:
        if next_state not in _ALLOWED_TRANSITIONS.get(prior_state, set()):
            raise ValueError(f"invalid publication transition {prior_state} -> {next_state}")
        cursor.execute(
            """
            UPDATE publish_intents
               SET state=%s,updated_at=CURRENT_TIMESTAMP
             WHERE intent_id=%s AND state=%s
            """,
            (next_state, str(intent_id), prior_state),
        )
        if cursor.rowcount != 1:
            raise RuntimeError(f"publication transition lost for {intent_id}")
        self._audit_insert(
            cursor,
            intent_id,
            f"publication.state.{next_state.lower()}",
            {"intent_id": str(intent_id), "prior_state": prior_state, "state": next_state, **payload},
            f"{base_key}:state:{next_state}",
        )

    def ensure_intent_created(self, reservation: LedgerReservation) -> LedgerReservation:
        if reservation.state == "INTENT_CREATED" or reservation.reused:
            return reservation
        intent_uuid = self._uuid(reservation.intent_id, "intent_id")
        with self._database._pool.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT state FROM publish_intents WHERE intent_id=%s FOR UPDATE",
                (str(intent_uuid),),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("publication intent does not exist")
            state = str(row[0])
            if state == "RESERVED":
                self._transition_locked(
                    cursor, intent_uuid, "RESERVED", "INTENT_CREATED",
                    reservation.idempotency_key, {"recovered": True},
                )
                state = "INTENT_CREATED"
            if state != "INTENT_CREATED":
                raise ValueError(f"publication intent is not ready for provider attempt: {state}")
        return LedgerReservation(
            intent_id=reservation.intent_id,
            publish_operation_id=reservation.publish_operation_id,
            state="INTENT_CREATED",
            account_id=reservation.account_id,
            platform=reservation.platform,
            platform_account_id=reservation.platform_account_id,
            idempotency_key=reservation.idempotency_key,
            publish_marker=reservation.publish_marker,
            reused=reservation.reused,
        )

    def begin_attempt(self, reservation: LedgerReservation, provider: str) -> LedgerAttempt:
        provider = str(provider or "").strip().lower()
        if not provider:
            raise ValueError("provider is required")
        intent_uuid = self._uuid(reservation.intent_id, "intent_id")
        attempt_uuid = uuid4()
        provider_key = f"{reservation.idempotency_key}:attempt"
        with self._database._pool.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT state FROM publish_intents WHERE intent_id=%s FOR UPDATE",
                (intent_uuid,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("publication intent does not exist")
            state = str(row[0])
            if state == "CALLING":
                cursor.execute(
                    """
                    SELECT attempt_id,attempt_number,provider,provider_idempotency_key
                    FROM publish_attempts
                    WHERE intent_id=%s
                    ORDER BY attempt_number DESC LIMIT 1
                    """,
                    (intent_uuid,),
                )
                existing = cursor.fetchone()
                if existing:
                    return LedgerAttempt(*(str(v) if i != 1 else int(v) for i, v in enumerate(existing)))
            if state != "INTENT_CREATED":
                raise ValueError(f"publication intent must be INTENT_CREATED before attempt; got {state}")
            cursor.execute(
                "SELECT COALESCE(MAX(attempt_number),0)+1 FROM publish_attempts WHERE intent_id=%s",
                (intent_uuid,),
            )
            attempt_number = int(cursor.fetchone()[0])
            cursor.execute(
                """
                INSERT INTO publish_attempts
                  (attempt_id,intent_id,attempt_number,started_at,call_deadline_at,
                   attempt_lease_expires_at,provider,provider_idempotency_key,status)
                VALUES (%s,%s,%s,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP + INTERVAL '5 minutes',
                        CURRENT_TIMESTAMP + INTERVAL '5 minutes',%s,%s,'STARTED')
                """,
                (str(attempt_uuid), str(intent_uuid), attempt_number, provider, provider_key),
            )
            self._transition_locked(
                cursor,
                intent_uuid,
                "INTENT_CREATED",
                "CALLING",
                reservation.idempotency_key,
                {"attempt_id": str(attempt_uuid), "attempt_number": attempt_number, "provider": provider},
            )
            return LedgerAttempt(
                attempt_id=str(attempt_uuid),
                intent_id=str(intent_uuid),
                attempt_number=attempt_number,
                provider=provider,
                provider_idempotency_key=provider_key,
            )

    def record_provider_result(self, attempt: LedgerAttempt, result: Any) -> str:
        intent_uuid = self._uuid(attempt.intent_id, "intent_id")
        attempt_uuid = self._uuid(attempt.attempt_id, "attempt_id")
        success = bool(getattr(result, "success", False))
        metadata = dict(getattr(result, "metadata", {}) or {})
        tracking_id = str(metadata.get("tracking_id") or "").strip()
        external_post_id = str(getattr(result, "post_id", "") or "").strip()
        url = str(getattr(result, "url", "") or "").strip()
        outcome_unknown = str(metadata.get("outcome") or "").lower() == "unknown"
        processing = str(metadata.get("publish_state") or "").lower() in {"processing", "pending"}
        explicit_outcome = str(metadata.get("outcome") or "").strip().lower()
        confirmed_failure = explicit_outcome in {
            "confirmed_failure", "failed_confirmed", "rejected", "rejected_confirmed",
        }
        if outcome_unknown:
            next_state = "OUTCOME_UNKNOWN"
            outcome = "AMBIGUOUS"
        elif success:
            next_state = "SUBMITTED"
            outcome = "ACCEPTED"
        elif processing and tracking_id:
            next_state = "SUBMITTED"
            outcome = "ACCEPTED_PROCESSING"
        elif confirmed_failure:
            next_state = "FAILED_CONFIRMED"
            outcome = "FAILED_CONFIRMED"
        else:
            next_state = "OUTCOME_UNKNOWN"
            outcome = "AMBIGUOUS"
        with self._database._pool.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT state FROM publish_intents WHERE intent_id=%s FOR UPDATE",
                (intent_uuid,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("publication intent does not exist")
            current = str(row[0])
            if current != "CALLING":
                raise ValueError(f"provider result requires CALLING state; got {current}")
            cursor.execute(
                """
                UPDATE publish_attempts
                   SET finished_at=CURRENT_TIMESTAMP,status=%s,outcome=%s,error_class=%s,error_message=%s,
                       updated_at=CURRENT_TIMESTAMP
                 WHERE attempt_id=%s
                """,
                (
                    "FINISHED" if not outcome_unknown else "UNKNOWN",
                    outcome,
                    None if success else str(getattr(result, "error_message", "") or "")[:100],
                    str(getattr(result, "error_message", "") or "")[:2000],
                    attempt_uuid,
                ),
            )
            cursor.execute(
                """
                INSERT INTO provider_effects
                  (effect_id,attempt_id,provider_tracking_id,external_post_id,external_url,provider_status,evidence)
                VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)
                """,
                (
                    uuid4(),
                    attempt_uuid,
                    tracking_id or None,
                    external_post_id or None,
                    url or None,
                    str(metadata.get("provider_status") or metadata.get("publish_state") or "") or None,
                    self._json(
                        {
                            "success": success,
                            "metadata": metadata,
                            "external_post_id_claimed": bool(external_post_id),
                        },
                        {},
                    ),
                ),
            )
            # Persist the provider effect identity without conflating tracking id
            # and public object id.  Verification remains a separate state.
            self._transition_locked(
                cursor,
                intent_uuid,
                current,
                next_state,
                f"{attempt.intent_id}:{attempt.attempt_number}",
                {
                    "attempt_id": attempt.attempt_id,
                    "tracking_id": tracking_id or None,
                    "external_post_id": external_post_id or None,
                    "outcome": outcome,
                },
            )
        return next_state

    def record_verification(
        self,
        intent_id: str,
        *,
        state: str,
        evidence: Dict[str, Any],
        next_reconcile_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
    ) -> str:
        state = str(state or "").strip().upper()
        allowed = {
            "VERIFIED_PUBLIC",
            "PUBLISHED_NOT_PUBLIC",
            "VERIFICATION_UNKNOWN",
            "IDENTITY_MISMATCH",
            "VERIFICATION_FAILED",
            "RECONCILING",
            "EXPIRED_UNVERIFIED",
        }
        if state not in allowed:
            raise ValueError(f"unsupported verification state {state}")
        intent_uuid = self._uuid(intent_id, "intent_id")
        with self._database._pool.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT state FROM publish_intents WHERE intent_id=%s FOR UPDATE", (intent_uuid,))
            row = cursor.fetchone()
            if not row:
                raise ValueError("publication intent does not exist")
            current = str(row[0])
            if state not in _ALLOWED_TRANSITIONS.get(current, set()):
                raise ValueError(f"invalid verification transition {current} -> {state}")
            cursor.execute(
                """
                INSERT INTO publication_verifications
                  (verification_id,intent_id,state,evidence,verified_at,next_reconcile_at,expires_at)
                VALUES (%s,%s,%s,%s::jsonb,%s,%s,%s)
                """,
                (
                    uuid4(),
                    intent_uuid,
                    state,
                    self._json(evidence, {}),
                    self._now_iso() if state == "VERIFIED_PUBLIC" else None,
                    next_reconcile_at,
                    expires_at,
                ),
            )
            cursor.execute(
                "SELECT idempotency_key FROM publish_intents WHERE intent_id=%s",
                (intent_uuid,),
            )
            base_key = str(cursor.fetchone()[0])
            self._transition_locked(
                cursor,
                intent_uuid,
                current,
                state,
                base_key,
                {"verification": evidence},
            )
        return state

    def get_provider_effect(self, intent_id: str) -> Optional[Dict[str, Any]]:
        intent_uuid = self._uuid(intent_id, "intent_id")
        return self._database._pool.query_one(
            """
            SELECT pe.*
            FROM provider_effects pe
            JOIN publish_attempts pa ON pa.attempt_id = pe.attempt_id
            WHERE pa.intent_id=%s
            ORDER BY pe.observed_at DESC
            LIMIT 1
            """,
            (intent_uuid,),
        )

    def record_operator_resolution(
        self,
        intent_id: str,
        actor_id: str,
        reason: str,
        evidence: Dict[str, Any],
        resulting_state: str,
    ) -> str:
        resulting_state = str(resulting_state or "").strip().upper()
        if resulting_state not in {"VERIFIED_PUBLIC", "FAILED_CONFIRMED", "RECONCILING"}:
            raise ValueError("operator resolution may only result in VERIFIED_PUBLIC, FAILED_CONFIRMED or RECONCILING")
        intent_uuid = self._uuid(intent_id, "intent_id")
        with self._database._pool.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT state,idempotency_key FROM publish_intents WHERE intent_id=%s FOR UPDATE",
                (intent_uuid,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("publication intent does not exist")
            prior_state, key = str(row[0]), str(row[1])
            if prior_state not in _UNRESOLVED | {"EXPIRED_UNVERIFIED"}:
                raise ValueError(f"operator resolution is not applicable to {prior_state}")
            if resulting_state == "RECONCILING" and prior_state not in {"EXPIRED_UNVERIFIED", "IDENTITY_MISMATCH", "VERIFICATION_FAILED", "VERIFICATION_UNKNOWN"}:
                raise ValueError(f"cannot reopen {prior_state} as RECONCILING")
            cursor.execute(
                """
                INSERT INTO operator_resolutions
                  (resolution_id,intent_id,actor_id,reason,evidence,prior_state,resulting_state)
                VALUES (%s,%s,%s,%s,%s::jsonb,%s,%s)
                """,
                (str(uuid4()), str(intent_uuid), actor_id, reason, self._json(evidence, {}), prior_state, resulting_state),
            )
            self._transition_locked(
                cursor, intent_uuid, prior_state, resulting_state, key,
                {"actor_id": actor_id, "reason": reason, "operator_evidence": evidence},
            )
        return resulting_state

    def get_intent(self, intent_id: str) -> Optional[Dict[str, Any]]:
        intent_uuid = self._uuid(intent_id, "intent_id")
        return self._database._pool.query_one(
            "SELECT * FROM publish_intents WHERE intent_id=%s",
            (intent_uuid,),
        )

    def has_unresolved(self, account_id: str, platform: str, platform_account_id: str) -> Optional[Dict[str, Any]]:
        return self._database._pool.query_one(
            """
            SELECT intent_id,state,created_at,updated_at,publish_operation_id
            FROM publish_intents
            WHERE account_id=%s AND platform=%s AND platform_account_id=%s
              AND state = ANY(%s)
            ORDER BY created_at DESC LIMIT 1
            """,
            (account_id, platform, platform_account_id, list(_UNRESOLVED)),
        )

    def unresolved_states(self) -> Iterable[str]:
        return tuple(sorted(_UNRESOLVED))
