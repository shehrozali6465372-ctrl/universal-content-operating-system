from datetime import datetime, timezone

import pytest

from agents.agent_02_trend_scout import TrendScoutAgent


NOW = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)


def pack(candidates):
    return {"account_id": "acct-1", "candidates": candidates}


def evidence(host, hours_ago=2, *, title="Recent report", content="A sufficiently detailed report about the observed topic."):
    published = NOW.replace(minute=0, second=0, microsecond=0).timestamp() - hours_ago * 3600
    stamp = datetime.fromtimestamp(published, timezone.utc).isoformat()
    return {"title": title, "content": content, "url": f"https://{host}/story", "published_at": stamp}


def test_ranks_recent_independent_evidence_and_hands_off_to_scoring():
    worker = TrendScoutAgent()
    result = worker.run(pack([{"topic": "Solar storage", "decision": "READY_FOR_VERIFICATION", "evidence": [evidence("one.example"), evidence("two.example", 5)]}]), as_of=NOW)
    assert result["status"] == "READY_FOR_SCORING"
    assert result["handoff"] == "AG08"
    assert result["ranked_trends"][0]["topic"] == "Solar storage"
    assert result["ranked_trends"][0]["independent_source_count"] == 2
    assert result["ranked_trends"][0]["trend_score"] > 0


def test_rejects_same_host_duplicates_and_old_or_untimestamped_evidence():
    worker = TrendScoutAgent()
    same_host = [evidence("publisher.example"), evidence("www.publisher.example", 3)]
    stale = evidence("old.example", 100)
    untimed = {"title": "Untimed", "content": "A sufficiently detailed report about this topic.", "url": "https://fresh.example/story"}
    result = worker.run(pack([{"topic": "Weak signal", "decision": "READY_FOR_VERIFICATION", "evidence": same_host + [stale, untimed]}]), as_of=NOW)
    assert result["status"] == "INSUFFICIENT_TREND_EVIDENCE"
    assert result["handoff"] is None
    assert result["ranked_trends"] == []


def test_missing_account_and_naive_clock_fail_closed():
    worker = TrendScoutAgent()
    with pytest.raises(ValueError, match="account_id"):
        worker.run({"candidates": []}, as_of=NOW)
    with pytest.raises(ValueError, match="timezone-aware"):
        worker.run(pack([]), as_of=datetime(2026, 10, 15, 12, 0))


def test_duplicate_topics_are_not_counted_twice():
    worker = TrendScoutAgent()
    item = {"topic": "Topic A", "decision": "READY_FOR_VERIFICATION", "evidence": [evidence("one.example"), evidence("two.example")]}
    result = worker.run(pack([item, item]), as_of=NOW)
    assert len(result["ranked_trends"]) == 1
    assert {row["reason"] for row in result["rejected_candidates"]} == {"duplicate_topic_in_pack"}


def test_held_upstream_candidate_is_never_promoted_to_trend():
    worker = TrendScoutAgent()
    result = worker.run(pack([{
        "topic": "Held topic",
        "decision": "HOLD_HISTORY_UNAVAILABLE",
        "evidence": [evidence("one.example"), evidence("two.example")],
    }]), as_of=NOW)
    assert result["status"] == "INSUFFICIENT_TREND_EVIDENCE"
    assert result["ranked_trends"] == []
    assert result["rejected_candidates"][0]["reason"] == "upstream_candidate_not_ready_for_verification"
