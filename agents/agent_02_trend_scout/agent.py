"""UCOS Agent 02: Trend Scout.

Ranks recent, attributable signals already collected by AG01. This worker does
not invent trend data or treat missing timestamps as current. It emits a
handoff to AG08 only when a topic has recent evidence from independent hosts.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlsplit


class TrendScoutAgent:
    """Rank evidence-backed trend signals from an AG01 research evidence pack."""

    agent_id = "AG02"
    name = "trend_scout"
    version = "1.0.0"

    def run(
        self,
        evidence_pack: Mapping[str, Any],
        *,
        as_of: datetime | None = None,
        window_hours: int = 72,
        min_independent_sources: int = 2,
    ) -> dict[str, Any]:
        """Return a deterministic trend report; missing/weak evidence fails closed.

        Input is the real AG01 evidence pack, not raw prompts or fabricated
        provider output. Each evidence record must include title, content, URL,
        and an ISO-8601 publication timestamp. Timestamps without timezone are
        rejected because their recency cannot be established safely.
        """
        if not isinstance(evidence_pack, Mapping):
            raise TypeError("evidence_pack must be a mapping")
        account_id = str(evidence_pack.get("account_id") or "").strip()
        if not account_id:
            raise ValueError("evidence_pack.account_id is required")
        if isinstance(window_hours, bool) or not isinstance(window_hours, int) or window_hours < 1:
            raise ValueError("window_hours must be a positive integer")
        if (
            isinstance(min_independent_sources, bool)
            or not isinstance(min_independent_sources, int)
            or min_independent_sources < 2
        ):
            raise ValueError("min_independent_sources must be at least 2")

        now = as_of or datetime.now(timezone.utc)
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        now = now.astimezone(timezone.utc)
        cutoff = now - timedelta(hours=window_hours)

        candidates = evidence_pack.get("candidates")
        if not isinstance(candidates, Sequence) or isinstance(candidates, (str, bytes)):
            raise ValueError("evidence_pack.candidates must be a sequence")

        ranked: list[dict[str, Any]] = []
        rejected: list[dict[str, str]] = []
        seen_topics: set[str] = set()

        for index, candidate in enumerate(candidates):
            if not isinstance(candidate, Mapping):
                rejected.append({"index": str(index), "reason": "candidate_not_a_mapping"})
                continue
            topic = str(candidate.get("topic") or candidate.get("title") or candidate.get("name") or "").strip()
            topic_key = " ".join(topic.casefold().split())
            if not topic_key:
                rejected.append({"index": str(index), "reason": "topic_missing"})
                continue
            if topic_key in seen_topics:
                rejected.append({"index": str(index), "reason": "duplicate_topic_in_pack"})
                continue
            seen_topics.add(topic_key)

            evidence = candidate.get("evidence")
            if not isinstance(evidence, Sequence) or isinstance(evidence, (str, bytes)):
                rejected.append({"topic": topic, "reason": "evidence_missing"})
                continue

            unique_hosts: dict[str, dict[str, Any]] = {}
            valid_times: list[datetime] = []
            evidence_refs: list[dict[str, str]] = []
            for item in evidence:
                if not isinstance(item, Mapping):
                    continue
                url = str(item.get("url") or item.get("source_url") or "").strip()
                title = str(item.get("title") or "").strip()
                content = str(item.get("content") or item.get("text") or item.get("snippet") or "").strip()
                if not title or not content or len(content) < 20:
                    continue
                try:
                    parts = urlsplit(url)
                    if parts.scheme not in {"http", "https"} or not parts.hostname:
                        continue
                    host = parts.hostname.lower().removeprefix("www.")
                    stamp_raw = str(item.get("published_at") or item.get("published_date") or "").strip()
                    if not stamp_raw:
                        continue
                    published = datetime.fromisoformat(stamp_raw.replace("Z", "+00:00"))
                    if published.tzinfo is None or published.utcoffset() is None:
                        continue
                    published = published.astimezone(timezone.utc)
                except (ValueError, TypeError):
                    continue
                if published < cutoff or published > now + timedelta(minutes=5):
                    continue
                if host in unique_hosts:
                    continue
                unique_hosts[host] = {
                    "host": host,
                    "title": title[:300],
                    "url": url[:2048],
                    "published_at": published.isoformat(),
                }
                valid_times.append(published)
                evidence_refs.append(unique_hosts[host])

            if len(unique_hosts) < min_independent_sources:
                rejected.append({
                    "topic": topic,
                    "reason": "insufficient_recent_independent_sources",
                })
                continue

            newest = max(valid_times)
            age_hours = max(0.0, (now - newest).total_seconds() / 3600.0)
            recency_score = max(0.0, 1.0 - age_hours / window_hours)
            diversity_score = min(1.0, len(unique_hosts) / 4.0)
            evidence_score = min(1.0, len(unique_hosts) / 5.0)
            score = round(100.0 * (0.55 * recency_score + 0.30 * diversity_score + 0.15 * evidence_score), 2)
            ranked.append({
                "topic": topic,
                "trend_score": score,
                "signal": "RECENT_MULTI_SOURCE_SIGNAL",
                "independent_source_count": len(unique_hosts),
                "newest_evidence_at": newest.isoformat(),
                "evidence": sorted(evidence_refs, key=lambda row: row["host"]),
                "score_components": {
                    "recency": round(recency_score, 4),
                    "source_diversity": round(diversity_score, 4),
                    "evidence_volume": round(evidence_score, 4),
                },
            })

        ranked.sort(key=lambda row: (-row["trend_score"], row["topic"].casefold()))
        return {
            "agent_id": self.agent_id,
            "agent_version": self.version,
            "account_id": account_id,
            "generated_at": now.isoformat(),
            "window_hours": window_hours,
            "status": "READY_FOR_SCORING" if ranked else "INSUFFICIENT_TREND_EVIDENCE",
            "handoff": "AG08" if ranked else None,
            "ranked_trends": ranked,
            "rejected_candidates": rejected,
            "limitations": [
                "Ranking reflects only the supplied AG01 evidence pack; it is not a claim of global search volume.",
                "Publication timestamps and independent publisher hosts are required for trend eligibility.",
                "This worker does not verify factual claims, write content, or authorize publication.",
            ],
        }
