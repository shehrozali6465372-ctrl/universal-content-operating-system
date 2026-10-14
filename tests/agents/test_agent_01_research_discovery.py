"""Contract tests for UCOS Agent 01: Research Discovery."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from agents.agent_01_research_discovery.agent import ResearchDiscoveryAgent


@pytest.fixture(autouse=True)
def _nonproduction_environment(monkeypatch):
    # These tests verify the worker contract without claiming live Neon access.
    monkeypatch.setenv("APP_ENV", "test")


class FakeTopicManager:
    def __init__(self):
        self.topics = {}

    def get_topic_by_name(self, name):
        return self.topics.get(name.casefold())

    def add_topic(self, name, **kwargs):
        item = {"name": name, **kwargs}
        self.topics[name.casefold()] = item
        return item


class FakeKnowledgeManager:
    def __init__(self):
        self.entries = []

    def collect(self, **kwargs):
        self.entries.append(kwargs)
        return {"stored": True}


class FakeVerifier:
    def __init__(self, status="verified", confidence=0.95):
        self.status = status
        self.confidence = confidence

    def verify_claim(self, claim_text, evidence_texts):
        return SimpleNamespace(
            status=self.status,
            confidence_result=SimpleNamespace(confidence=self.confidence),
        )


class FakeMemoryManager:
    def __init__(self):
        self.entries = []

    def store_entry(self, **kwargs):
        self.entries.append(kwargs)
        return kwargs["entry_id"]


class FakeScoringManager:
    def score_topic(self, topic, niche="general", scores=None, evidence=None):
        return {
            "topic": topic,
            "niche": niche,
            "overall_score": 8.5,
            "recommendation": "publish",
            "confidence": 0.95,
            "raw_scores": scores or {},
            "weighted_scores": {},
        }


class FakePlanner:
    def create_plan(self, topic, niche="general"):
        return SimpleNamespace(plan_id="plan-test", status="ready", tasks=[object()])


def build_agent(tmp_path, *, history=None, history_error=False, writes=None, verifier=None):
    writes = writes if writes is not None else []
    account = {"account_id": "account-a", "platform": "pinterest", "niche": "home decor", "enabled": True}

    def read_history(account_id):
        assert account_id == "account-a"
        if history_error:
            raise RuntimeError("deliberate test failure")
        return list(history or [])

    components = {
        "topic_manager": FakeTopicManager(),
        "knowledge_manager": FakeKnowledgeManager(),
        "verifier": verifier or FakeVerifier(),
        "memory_manager": FakeMemoryManager(),
        "scoring_manager": FakeScoringManager(),
        "planner_manager": FakePlanner(),
    }
    return ResearchDiscoveryAgent(
        "account-a",
        account_resolver=lambda account_id: account,
        history_reader=read_history,
        result_writer=writes.append,
        storage_root=tmp_path,
        components=components,
    ), writes, components


def supported_candidate(topic="Small-space storage ideas"):
    return {
        "topic": topic,
        "scores": {"audience_fit": 8, "opportunity": 8, "risk": 2},
        "claims": ["Two independent sources support this claim."],
        "evidence": [
            {
                "source": "Source One",
                "title": "Research one",
                "url": "https://one.example.com/article",
                "content": "The first source contains directly relevant supporting evidence.",
            },
            {
                "source": "Source Two",
                "title": "Research two",
                "url": "https://two.example.org/research",
                "content": "The second independent source contains corroborating evidence.",
            },
        ],
    }


def test_missing_account_id_is_rejected():
    with pytest.raises(ValueError, match="account_id is required"):
        ResearchDiscoveryAgent("", account_resolver=lambda _account_id: None)


def test_supported_candidate_is_ready_for_writing_review_not_publication(tmp_path):
    agent, writes, components = build_agent(tmp_path)
    report = agent.run([supported_candidate()])

    assert report["status"] == "completed"
    assert report["account_id"] == "account-a"
    assert report["recommended_topic"] == "Small-space storage ideas"
    candidate = report["candidates"][0]
    assert candidate["decision"] == "READY_FOR_WRITING_REVIEW"
    assert candidate["verification"]["status"] == "verified"
    assert candidate["independent_source_count"] == 2
    assert report["publishing"] == {"performed": False, "status": "not_requested"}
    assert report["persistence"]["status"] == "persisted"
    assert len(writes) == 1
    assert len(components["knowledge_manager"].entries) == 2


def test_published_topic_in_account_history_is_blocked(tmp_path):
    agent, _writes, _components = build_agent(
        tmp_path,
        history=[{
            "topic": "Small-space storage ideas",
            "text": "Previously published copy.",
            "published": True,
            "post_id": "real-post-123",
        }],
    )
    report = agent.run([supported_candidate()])

    candidate = report["candidates"][0]
    assert candidate["decision"] == "BLOCK_DUPLICATE_PUBLISHED"
    assert candidate["duplicate"]["post_id_present"] is True
    assert report["recommended_topic"] is None


def test_unavailable_history_fails_closed(tmp_path):
    agent, _writes, _components = build_agent(tmp_path, history_error=True)
    report = agent.run([supported_candidate()])

    assert report["history"]["status"] == "unknown"
    assert report["candidates"][0]["decision"] == "HOLD_HISTORY_UNAVAILABLE"
    assert report["recommended_topic"] is None


def test_duplicate_candidate_in_same_batch_is_blocked(tmp_path):
    agent, _writes, _components = build_agent(tmp_path)
    report = agent.run([
        supported_candidate("Small-space storage ideas"),
        supported_candidate("Small-space storage ideas"),
    ])

    assert report["candidate_count"] == 2
    assert report["candidates"][1]["decision"] == "BLOCK_DUPLICATE_IN_BATCH"


def test_same_source_host_does_not_count_as_two_independent_sources(tmp_path):
    agent, _writes, _components = build_agent(tmp_path)
    candidate = supported_candidate()
    candidate["evidence"][1]["url"] = "https://one.example.com/another-page"

    report = agent.run([candidate])

    result = report["candidates"][0]
    assert result["evidence_count"] == 1
    assert result["decision"] == "NEEDS_MORE_EVIDENCE"


def test_low_confidence_claim_cannot_be_marked_ready(tmp_path):
    agent, _writes, _components = build_agent(
        tmp_path,
        verifier=FakeVerifier(status="verified", confidence=0.40),
    )
    report = agent.run([supported_candidate()])

    assert report["candidates"][0]["decision"] == "HUMAN_REVIEW_REQUIRED"
    assert report["recommended_topic"] is None


def test_invalid_limit_is_rejected(tmp_path):
    agent, _writes, _components = build_agent(tmp_path)
    with pytest.raises(ValueError, match="limit must be a positive integer"):
        agent.run([], limit=0)

def test_empty_production_namespace_does_not_claim_history_is_complete(tmp_path, monkeypatch):
    import layers.layer07_publishing.modules.account_control.account_data_store as account_store_module

    class MissingBaselineStore:
        def __init__(self, registry=None):
            self.registry = registry

        def bootstrap_legacy_store(self, account_id, kind):
            return {"status": "legacy_store_missing", "records_imported": 0}

        def get(self, account_id, kind, key, default=None):
            return default

    monkeypatch.setattr(account_store_module, "AccountDataStore", MissingBaselineStore)
    agent, _writes, _components = build_agent(tmp_path)
    agent._history_reader = None
    agent._get_registry = lambda: object()
    monkeypatch.setenv("APP_ENV", "production")

    rows, available, error_code = agent._load_history()

    assert rows == []
    assert available is False
    assert error_code == "history_baseline_not_verified"

def test_unconfigured_sources_are_reported_explicitly(tmp_path):
    agent, _writes, _components = build_agent(tmp_path)

    report = agent.run()

    assert report["status"] == "blocked_research_sources_unconfigured"
    assert report["research_sources"]["status"] == "unconfigured"
    assert "research_sources_unconfigured" in report["warnings"]

def test_unavailable_history_short_circuits_research_side_effects(tmp_path):
    agent, _writes, components = build_agent(tmp_path, history_error=True)

    report = agent.run([supported_candidate()])

    assert report["candidates"][0]["decision"] == "HOLD_HISTORY_UNAVAILABLE"
    assert components["knowledge_manager"].entries == []
    assert components["memory_manager"].entries == []
    assert components["topic_manager"].topics == {}


def test_evidence_without_a_traceable_url_is_not_counted(tmp_path):
    agent, _writes, _components = build_agent(tmp_path)
    candidate = supported_candidate()
    candidate["evidence"][1]["url"] = ""

    report = agent.run([candidate])

    assert report["candidates"][0]["evidence_count"] == 1
    assert report["candidates"][0]["decision"] == "NEEDS_MORE_EVIDENCE"
