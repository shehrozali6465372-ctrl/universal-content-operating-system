"""Frozen v1.2 publication ledger contract tests against real PostgreSQL."""
from __future__ import annotations

import os
import uuid

import pytest

from layers.layer07_publishing.modules.publisher_engine.publication_ledger import (
    PublicationConflictError,
    PublicationLedger,
    UnresolvedPublicationError,
)
from layers.layer07_publishing.modules.publisher_engine.publish_request import PublishRequest
from layers.layer13_persistence.modules.postgresql.manager import PostgreSQLManager


def _manager() -> PostgreSQLManager:
    manager = PostgreSQLManager()
    assert manager.initialize() is True
    return manager


def _request(account_id: str, platform_account_id: str, workflow_id: str, content: str) -> PublishRequest:
    req = PublishRequest(platform="facebook", content=content, content_type="post")
    req.idempotency_key = f"test:{account_id}:{workflow_id}"
    req.metadata.update({
        "account_id": account_id,
        "tenant_id": f"tenant-{account_id}",
        "workspace_id": f"workspace-{account_id}",
        "brand_id": f"brand-{account_id}",
        "platform_account_id": platform_account_id,
        "workflow_id": workflow_id,
        "publish_mode": "production",
        "policy_snapshot": {"version": "test-v1.2"},
    })
    return req


def _cleanup(manager: PostgreSQLManager, intent_id: str, workflow_id: str) -> None:
    pool = manager._pool
    assert pool is not None
    with pool.transaction() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM operator_resolutions WHERE intent_id=%s",
            (uuid.UUID(intent_id),),
        )
        cur.execute(
            "DELETE FROM publication_verifications WHERE intent_id=%s",
            (uuid.UUID(intent_id),),
        )
        cur.execute(
            "DELETE FROM provider_effects WHERE attempt_id IN "
            "(SELECT attempt_id FROM publish_attempts WHERE intent_id=%s)",
            (uuid.UUID(intent_id),),
        )
        cur.execute(
            "DELETE FROM publish_attempts WHERE intent_id=%s",
            (uuid.UUID(intent_id),),
        )
        cur.execute(
            "DELETE FROM publish_intents WHERE intent_id=%s",
            (uuid.UUID(intent_id),),
        )
        cur.execute(
            "DELETE FROM outbox_events WHERE aggregate_type='publish_intent' "
            "AND aggregate_id=%s",
            (uuid.UUID(intent_id),),
        )
        cur.execute(
            "DELETE FROM workflow_runs WHERE workflow_id=%s",
            (uuid.UUID(workflow_id),),
        )


@pytest.mark.integration
def test_atomic_idempotency_and_unresolved_gate() -> None:
    manager = _manager()
    ledger = PublicationLedger(manager)
    account = f"ledger-{uuid.uuid4().hex}"
    platform_account = f"page-{uuid.uuid4().hex}"
    workflow = str(uuid.uuid4())
    req = _request(account, platform_account, workflow, "canonical publication content")
    try:
        first = ledger.reserve(req)
        assert first.reused is False
        assert first.state == "INTENT_CREATED"

        same = ledger.reserve(req)
        assert same.reused is True
        assert same.intent_id == first.intent_id

        conflict = _request(account, platform_account, workflow, "different content")
        with pytest.raises(PublicationConflictError):
            ledger.reserve(conflict)

        attempt = ledger.begin_attempt(first, "facebook")
        intent = ledger.get_intent(first.intent_id)
        assert intent is not None
        assert intent["state"] == "CALLING"
        assert attempt.attempt_number == 1

        ambiguous = type("ProviderResult", (), {
            "success": False,
            "post_id": "",
            "url": "",
            "error_message": "network timeout",
            "metadata": {"outcome": "unknown"},
        })()
        state = ledger.record_provider_result(attempt, ambiguous)
        assert state == "OUTCOME_UNKNOWN"

        with pytest.raises(UnresolvedPublicationError):
            ledger.reserve(_request(account, platform_account, str(uuid.uuid4()), "new logical publication"))

        ledger.record_verification(
            first.intent_id,
            state="RECONCILING",
            evidence={"reason": "retry reconciliation"},
        )
        assert ledger.get_intent(first.intent_id)["state"] == "RECONCILING"

        ledger.record_verification(
            first.intent_id,
            state="VERIFIED_PUBLIC",
            evidence={"provider": "facebook", "external_post_id": "post-1", "canonical_url": "https://example.test/post-1"},
        )
        assert ledger.get_intent(first.intent_id)["state"] == "VERIFIED_PUBLIC"
    finally:
        _cleanup(manager, first.intent_id if "first" in locals() else str(uuid.uuid4()), workflow)
        manager.close()


@pytest.mark.integration
def test_unclassified_provider_failure_never_becomes_confirmed_failure() -> None:
    manager = _manager()
    ledger = PublicationLedger(manager)
    account = f"ledger-unknown-{uuid.uuid4().hex}"
    platform_account = f"page-{uuid.uuid4().hex}"
    workflow = str(uuid.uuid4())
    req = _request(account, platform_account, workflow, "ambiguous failure")
    try:
        reservation = ledger.reserve(req)
        attempt = ledger.begin_attempt(reservation, "facebook")
        result = type("ProviderResult", (), {
            "success": False,
            "post_id": "",
            "url": "",
            "error_message": "provider returned a non-specific error",
            "metadata": {},
        })()
        assert ledger.record_provider_result(attempt, result) == "OUTCOME_UNKNOWN"
    finally:
        _cleanup(manager, reservation.intent_id if "reservation" in locals() else str(uuid.uuid4()), workflow)
        manager.close()


@pytest.mark.integration
def test_production_reservation_requires_full_identity_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    manager = _manager()
    ledger = PublicationLedger(manager)
    workflow = str(uuid.uuid4())
    req = PublishRequest(platform="facebook", content="identity gate", content_type="post")
    req.idempotency_key = f"identity:{uuid.uuid4()}"
    req.metadata.update({
        "account_id": "account-without-tenant",
        "workflow_id": workflow,
        "publish_mode": "production",
    })
    try:
        with pytest.raises(ValueError, match="tenant_id"):
            ledger.reserve(req)
    finally:
        manager.close()
