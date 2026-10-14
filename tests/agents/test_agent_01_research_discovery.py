"""Agent 01 contract tests: discovery, account history, and evidence-pack handoff."""
from __future__ import annotations

import pytest

from agents.agent_01_research_discovery.agent import ResearchDiscoveryAgent


@pytest.fixture(autouse=True)
def _test_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)


class InMemoryAccountStore:
    def __init__(self):
        self.data = {}

    def get(self, account_id, kind, key, default=None):
        return self.data.get((account_id, kind, key), default)

    def put(self, account_id, kind, key, value):
        self.data[(account_id, kind, key)] = value


def candidate(topic="Small-space storage ideas"):
    return {
        "topic": topic,
        "source_relevance_score": 0.86,
        "claims": ["The writing agent should verify this factual claim."],
        "evidence": [
            {
                "source": "publisher-one.example",
                "title": "Storage research one",
                "url": "https://publisher-one.example/article",
                "content": "A source-backed excerpt about small-space storage.",
                "published_at": "2026-10-13",
            },
            {
                "source": "publisher-two.example",
                "title": "Storage research two",
                "url": "https://publisher-two.example/research",
                "content": "A second independent excerpt about apartment storage.",
            },
        ],
    }


def build_agent(
    tmp_path,
    *,
    history=None,
    history_error=False,
    writes=None,
    candidate_provider=None,
    evidence_provider=None,
    account_store=None,
):
    writes = writes if writes is not None else []
    account = {
        "account_id": "account-a",
        "platform": "pinterest",
        "niche": "home decor",
        "enabled": True,
    }

    def read_history(account_id):
        assert account_id == "account-a"
        if history_error:
            raise RuntimeError("deliberate test failure")
        return list(history or [])

    kwargs = {
        "account_resolver": lambda account_id: account,
        "history_reader": read_history,
        "result_writer": writes.append,
        "candidate_provider": candidate_provider,
        "evidence_provider": evidence_provider,
        "account_store": account_store,
    }
    if account_store is None:
        kwargs["storage_root"] = tmp_path
    return ResearchDiscoveryAgent("account-a", **kwargs), writes


def test_missing_account_id_is_rejected():
    with pytest.raises(ValueError, match="account_id is required"):
        ResearchDiscoveryAgent("")


def test_supported_candidate_is_handed_to_agent_06_not_publishing(tmp_path):
    agent, writes = build_agent(tmp_path)
    report = agent.run([candidate()])

    result = report["candidates"][0]
    assert report["status"] == "completed"
    assert report["account_id"] == "account-a"
    assert report["recommended_topic"] == "Small-space storage ideas"
    assert result["decision"] == "READY_FOR_VERIFICATION"
    assert result["verification"]["status"] == "pending_agent_06"
    assert result["claims_for_agent_06"] == ["The writing agent should verify this factual claim."]
    assert result["evidence_count"] == 2
    assert result["independent_source_count"] == 2
    assert result["source_relevance"]["value"] == pytest.approx(0.86)
    assert result["source_relevance"]["metric"] == "vendor_search_relevance_not_content_performance"
    assert result["next_agent"] == "AG06"
    assert report["publishing"] == {"performed": False, "status": "not_requested"}
    assert report["persistence"]["status"] == "persisted"
    assert len(writes) == 1


def test_published_topic_in_account_history_is_blocked_before_research(tmp_path):
    calls = []
    agent, _writes = build_agent(
        tmp_path,
        history=[{
            "topic": "Small-space storage ideas",
            "text": "Previously published copy.",
            "published": True,
            "post_id": "real-post-123",
        }],
        evidence_provider=lambda topic, niche, limit: calls.append(topic) or [],
    )
    report = agent.run([candidate()])

    result = report["candidates"][0]
    assert result["decision"] == "BLOCK_DUPLICATE_PUBLISHED"
    assert result["duplicate"]["post_id_present"] is True
    assert result["evidence_count"] == 0
    assert calls == []
    assert report["recommended_topic"] is None


def test_unavailable_history_fails_closed_without_research_side_effects(tmp_path):
    calls = []
    agent, _writes = build_agent(
        tmp_path,
        history_error=True,
        evidence_provider=lambda topic, niche, limit: calls.append(topic) or [],
    )
    report = agent.run([candidate()])

    assert report["history"]["status"] == "unknown"
    assert report["candidates"][0]["decision"] == "HOLD_HISTORY_UNAVAILABLE"
    assert calls == []
    assert report["recommended_topic"] is None


def test_duplicate_candidate_in_same_batch_is_blocked(tmp_path):
    agent, _writes = build_agent(tmp_path)
    report = agent.run([candidate(), candidate()])

    assert report["candidate_count"] == 2
    assert report["candidates"][1]["decision"] == "BLOCK_DUPLICATE_IN_BATCH"


def test_same_source_host_is_not_counted_as_two_independent_sources(tmp_path):
    agent, _writes = build_agent(tmp_path)
    repeated_host = candidate()
    repeated_host["evidence"][1]["url"] = "https://publisher-one.example/another-page"

    report = agent.run([repeated_host])

    result = report["candidates"][0]
    assert result["evidence_count"] == 1
    assert result["decision"] == "NEEDS_MORE_EVIDENCE"


def test_missing_source_url_does_not_count_as_citable_evidence(tmp_path):
    agent, _writes = build_agent(tmp_path)
    value = candidate()
    value["evidence"][1]["url"] = ""

    report = agent.run([value])

    assert report["candidates"][0]["evidence_count"] == 1
    assert report["candidates"][0]["decision"] == "NEEDS_MORE_EVIDENCE"


def test_evidence_provider_can_add_a_second_independent_source(tmp_path):
    value = candidate()
    value["evidence"] = value["evidence"][:1]
    agent, _writes = build_agent(
        tmp_path,
        evidence_provider=lambda topic, niche, limit: [{
            "source": "publisher-two.example",
            "title": "Second source",
            "url": "https://publisher-two.example/support",
            "content": "Supporting source material.",
        }],
    )

    report = agent.run([value])

    assert report["candidates"][0]["evidence_count"] == 2
    assert report["candidates"][0]["decision"] == "READY_FOR_VERIFICATION"


def test_unconfigured_source_is_reported_explicitly(tmp_path):
    agent, _writes = build_agent(tmp_path)

    report = agent.run()

    assert report["status"] == "blocked_research_sources_unconfigured"
    assert report["research_sources"]["status"] == "unconfigured"


def test_failed_candidate_provider_is_reported_as_unavailable(tmp_path):
    def fail_provider(account_id, niche, limit):
        raise RuntimeError("provider secret details must not leak")

    agent, _writes = build_agent(tmp_path, candidate_provider=fail_provider)

    report = agent.run()

    assert report["status"] == "blocked_research_sources_unavailable"
    assert report["research_sources"]["status"] == "unavailable"
    assert "provider secret details" not in str(report)


def test_invalid_limit_is_rejected(tmp_path):
    agent, _writes = build_agent(tmp_path)
    with pytest.raises(ValueError, match="limit must be a positive integer"):
        agent.run([], limit=0)


def test_unconfigured_durable_state_prevents_ready_handoff(tmp_path):
    writes = []
    account = {"account_id": "account-isolated", "platform": "pinterest", "niche": "home decor", "enabled": True}
    agent = ResearchDiscoveryAgent(
        "account-isolated",
        account_resolver=lambda _account_id: account,
        history_reader=lambda _account_id: [],
        result_writer=writes.append,
    )

    report = agent.run([candidate()])

    assert report["candidates"][0]["decision"] == "HOLD_RESEARCH_STORAGE_UNAVAILABLE"
    assert report["recommended_topic"] is None


def test_account_scoped_state_persists_topic_evidence_and_run_by_account(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    store = InMemoryAccountStore()
    store.put("account-a", "memory", "history_baseline:content:v1", {
        "status": "complete",
        "source": "operator_review",
        "records_checked": 0,
    })
    account = {"account_id": "account-a", "platform": "pinterest", "niche": "home decor", "enabled": True}
    agent = ResearchDiscoveryAgent(
        "account-a",
        account_resolver=lambda _account_id: account,
        account_store=store,
    )

    report = agent.run([candidate()])

    assert report["candidates"][0]["decision"] == "READY_FOR_VERIFICATION"
    assert report["persistence"]["status"] == "persisted"
    keys = [key for (account_id, kind, key) in store.data if account_id == "account-a" and kind == "memory"]
    assert any(key.startswith("research_candidate:") for key in keys)
    assert len([key for key in keys if key.startswith("research_evidence:")]) == 2
    assert any(key.startswith("research_agent_run:") for key in keys)
    assert all(account_id == "account-a" for account_id, _kind, _key in store.data)


def test_two_accounts_have_separate_research_state(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    store = InMemoryAccountStore()

    def make(account_id):
        account = {"account_id": account_id, "platform": "pinterest", "niche": "home decor", "enabled": True}
        return ResearchDiscoveryAgent(
            account_id,
            account_resolver=lambda _account_id: account,
            history_reader=lambda _account_id: [],
            account_store=store,
        )

    make("account-a").run([candidate("Ideas for account A")])
    make("account-b").run([candidate("Ideas for account B")])

    topics_a = [
        value for (account_id, kind, key), value in store.data.items()
        if account_id == "account-a" and key.startswith("research_candidate:")
    ]
    topics_b = [
        value for (account_id, kind, key), value in store.data.items()
        if account_id == "account-b" and key.startswith("research_candidate:")
    ]
    assert [row["topic"] for row in topics_a] == ["Ideas for account A"]
    assert [row["topic"] for row in topics_b] == ["Ideas for account B"]



def test_production_with_unknown_history_baseline_blocks_before_live_search(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("TAVILY_API_KEY", "unit-test-config-only")
    store = InMemoryAccountStore()
    account = {"account_id": "account-a", "platform": "pinterest", "niche": "home decor", "enabled": True}
    agent = ResearchDiscoveryAgent(
        "account-a",
        account_resolver=lambda _account_id: account,
        account_store=store,
    )
    assert agent._source is not None
    assert agent._source.request_count == 0

    # Exercise the production fail-closed branch without sending an HTTP request.
    monkeypatch.setenv("APP_ENV", "production")
    report = agent.run()

    assert report["status"] == "blocked_history_unavailable"
    assert report["history"]["status"] == "unknown"
    assert report["candidate_count"] == 0
    assert report["recommended_topic"] is None
    assert agent._source.request_count == 0
    assert not any(key.startswith("research_candidate:") for (_aid, _kind, key) in store.data)


def test_agent_01_has_no_imports_from_legacy_research_layer():
    from pathlib import Path
    import inspect

    path = Path(inspect.getsourcefile(ResearchDiscoveryAgent))
    source = path.read_text(encoding="utf-8")
    assert "layers.layer02_research" not in source


def test_production_refuses_injected_account_provider_and_storage_dependencies(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("TAVILY_API_KEY", "unit-test-config-only")
    store = InMemoryAccountStore()
    account = {"account_id": "account-a", "platform": "pinterest", "niche": "home decor", "enabled": True}

    with pytest.raises(ValueError, match="production mode forbids injected test dependencies"):
        ResearchDiscoveryAgent(
            "account-a",
            account_resolver=lambda _account_id: account,
            history_reader=lambda _account_id: [],
            candidate_provider=lambda *_args: [candidate()],
            evidence_provider=lambda *_args: candidate()["evidence"],
            result_writer=lambda _report: None,
            account_store=store,
        )


def test_production_rejects_caller_supplied_candidates(monkeypatch, tmp_path):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("TAVILY_API_KEY", "unit-test-config-only")
    account = {"account_id": "account-a", "platform": "pinterest", "niche": "home decor", "enabled": True}
    agent = ResearchDiscoveryAgent(
        "account-a",
        account_resolver=lambda _account_id: account,
        history_reader=lambda _account_id: [],
        storage_root=tmp_path,
    )
    monkeypatch.setenv("APP_ENV", "production")

    with pytest.raises(ValueError, match="caller-supplied candidates"):
        agent.run([candidate()])
