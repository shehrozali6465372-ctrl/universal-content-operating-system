"""Adversarial production gates for UCOS Layer 23."""
from __future__ import annotations

import json
import sqlite3
import uuid

import pytest

import layers.layer23_website_manager.integration.atoz_bridge as bridge
from layers.layer23_website_manager.services.publisher import Publisher
from layers.layer23_website_manager.models.article import ArticleStatus
from layers.layer23_website_manager.website_manager import get_website


def _payload(**context):
    return {
        "request_id": str(uuid.uuid4()),
        "niche_id": str(uuid.uuid4()),
        "job_type": "content",
        "context": {
            "domain": "production-gate.example",
            "site_name": "Production Gate",
            **context,
        },
    }


def test_failed_claim_is_terminal_and_replay_is_deterministic(monkeypatch, tmp_path):
    db_path = tmp_path / "job-inbox.sqlite3"
    monkeypatch.setattr(bridge, "_INBOX_DB", db_path)

    payload = _payload(title="", content="")
    with pytest.raises(ValueError, match="content jobs require"):
        bridge.dispatch_job(payload)

    with sqlite3.connect(db_path) as db:
        row = db.execute(
            "SELECT state, response_json FROM job_inbox WHERE request_id=?",
            (payload["request_id"],),
        ).fetchone()

    assert row is not None
    assert row[0] == "failed"
    assert json.loads(row[1])["state"] == "failed"

    replay = bridge.dispatch_job(payload)
    assert replay["state"] == "failed"
    assert replay["request_id"] == payload["request_id"]


def test_payload_conflict_is_rejected(monkeypatch, tmp_path):
    db_path = tmp_path / "job-inbox.sqlite3"
    monkeypatch.setattr(bridge, "_INBOX_DB", db_path)

    request_id = str(uuid.uuid4())
    first = _payload(title="first", content="body")
    first["request_id"] = request_id

    bridge._init_inbox()
    cached, lease = bridge._claim_request(request_id, bridge._payload_hash(first))
    assert cached is None
    assert bridge._finish_request(
        request_id, lease, {"state": "succeeded", "request_id": request_id}
    )

    second = dict(first)
    second["context"] = dict(first["context"], content="different")
    with pytest.raises(ValueError, match="replay conflict"):
        bridge.dispatch_job(second)


def test_stale_worker_cannot_finish_recovered_request(monkeypatch, tmp_path):
    db_path = tmp_path / "job-inbox.sqlite3"
    monkeypatch.setattr(bridge, "_INBOX_DB", db_path)

    request_id = str(uuid.uuid4())
    bridge._init_inbox()
    cached, old_lease = bridge._claim_request(request_id, "hash")
    assert cached is None

    with sqlite3.connect(db_path) as db:
        db.execute(
            "UPDATE job_inbox SET lease_expires_at=? WHERE request_id=?",
            (0.0, request_id),
        )
        db.commit()

    cached, new_lease = bridge._claim_request(request_id, "hash")
    assert cached is None
    assert new_lease != old_lease
    assert not bridge._finish_request(
        request_id, old_lease, {"state": "succeeded", "worker": "stale"}
    )
    assert bridge._finish_request(
        request_id, new_lease, {"state": "succeeded", "worker": "current"}
    )

    with sqlite3.connect(db_path) as db:
        response = json.loads(
            db.execute(
                "SELECT response_json FROM job_inbox WHERE request_id=?",
                (request_id,),
            ).fetchone()[0]
        )
    assert response["worker"] == "current"


def test_website_instances_are_isolated_by_identity():
    site_a = get_website(
        domain=f"a-{uuid.uuid4().hex}.example",
        site_name="Site A",
    )
    site_b = get_website(
        domain=f"b-{uuid.uuid4().hex}.example",
        site_name="Site B",
    )
    assert site_a is not site_b
    assert site_a.get_config().domain != site_b.get_config().domain


def test_article_store_survives_restart(tmp_path):
    storage = tmp_path / "articles"
    first = Publisher(storage_dir=str(storage))
    article = first.create_article(
        "Durable Article",
        content="content must survive restart",
        status=ArticleStatus.PUBLISHED,
    )

    second = Publisher(storage_dir=str(storage))
    restored = second.get_article(article.article_id)

    assert restored is not None
    assert restored.title == "Durable Article"
    assert restored.content == "content must survive restart"
    assert restored.status == ArticleStatus.PUBLISHED


def test_publisher_writes_complete_atomic_state(tmp_path):
    storage = tmp_path / "articles"
    publisher = Publisher(storage_dir=str(storage))
    article = publisher.create_article("Atomic", "body")
    publisher.update_article(article.article_id, content="updated")

    persisted = json.loads((storage / "articles.json").read_text(encoding="utf-8"))
    assert persisted[0]["content"] == "updated"
    assert persisted[0]["status"] == "draft"
    assert not (storage / "articles.json.tmp").exists()
