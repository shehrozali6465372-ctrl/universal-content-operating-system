"""Task-scoped adapters from the single Research Agent to existing Layer 02 modules.

External retrieval is owned by Layer 11's IntegrationGateway. These bindings call
that real search transport and feed its returned source records through Layer 02.
No fallback generates made-up search results or quantitative market metrics.
"""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable, Mapping
from urllib.parse import urlparse

from layers.layer02_research.modules.audience_research.audience_intel_manager import AudienceIntelManager
from layers.layer02_research.modules.competitor_analysis.competitor_intel_manager import CompetitorIntelManager
from layers.layer02_research.modules.competitor_analysis.content_analyzer import ContentPost
from layers.layer02_research.modules.fact_verification.verification_manager import VerificationManager
from layers.layer02_research.modules.knowledge_collector.knowledge_collector_manager import KnowledgeCollectorManager
from layers.layer02_research.modules.research_memory.research_memory_manager import ResearchMemoryManager
from layers.layer02_research.modules.topic_intelligence.topic_entry import TopicEntry
from layers.layer02_research.modules.topic_intelligence.topic_intel_manager import TopicIntelManager
from layers.layer02_research.modules.trend_discovery.trend_manager import TrendManager

_STOP_WORDS = {
    "about", "after", "again", "also", "among", "because", "been", "before",
    "being", "best", "could", "does", "from", "have", "into", "just", "more",
    "most", "much", "over", "same", "should", "some", "such", "than", "that",
    "their", "there", "these", "they", "this", "those", "through", "under",
    "very", "what", "when", "where", "which", "while", "with", "would",
    "your", "using", "used", "latest", "news", "trends", "trend", "review",
    "reviews", "guide", "guides", "best", "ways", "need", "needs", "today",
}


def _valid_source_url(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    parsed = urlparse(value.strip())
    return (
        parsed.scheme in {"http", "https"}
        and bool(parsed.hostname)
        and not parsed.username
        and not parsed.password
    )


def _keywords(text: str, limit: int = 18) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9'-]{2,}", text.casefold())
    output = []
    seen = set()
    for word in words:
        word = word.strip("'-")
        if len(word) < 3 or word in _STOP_WORDS or word in seen:
            continue
        seen.add(word)
        output.append(word)
        if len(output) >= limit:
            break
    return output


def _search(gateway: Any, query: str, *, limit: int = 8) -> dict[str, Any]:
    """Use the configured live Layer 11 search provider; validate returned shape."""
    response = gateway.search(query)
    if not isinstance(response, Mapping):
        raise RuntimeError("Layer 11 search gateway returned a non-object response")
    provider = str(response.get("provider") or response.get("source") or "unknown")
    raw_results = response.get("results")
    if not isinstance(raw_results, list):
        raise RuntimeError("Layer 11 search gateway response has no results array")

    sources = []
    seen_urls = set()
    for position, item in enumerate(raw_results, start=1):
        if not isinstance(item, Mapping):
            continue
        url = item.get("link") or item.get("url") or item.get("source_url")
        if not _valid_source_url(url):
            continue
        url = url.strip()
        if url in seen_urls:
            continue
        seen_urls.add(url)
        sources.append({
            "url": url,
            "title": str(item.get("title") or "Untitled source")[:500],
            "snippet": str(item.get("snippet") or item.get("description") or "")[:3000],
            "position": item.get("position", position),
            "provider": provider,
            "observed_at": datetime.now(timezone.utc).isoformat(),
        })
        if len(sources) >= limit:
            break

    if not sources:
        raise RuntimeError(f"Layer 11 search gateway returned no usable source URLs for query: {query}")
    return {"query": query, "provider": provider, "sources": sources}


def _upstream(context: Mapping[str, Any], module: str) -> dict[str, Any]:
    results = context.get("upstream_results", {})
    if not isinstance(results, Mapping):
        return {}
    value = results.get(module, {})
    return value if isinstance(value, dict) else {}


def _combine_sources(*modules: Mapping[str, Any]) -> list[dict[str, Any]]:
    combined: dict[str, dict[str, Any]] = {}
    for module in modules:
        for source in module.get("sources", []) or []:
            if isinstance(source, Mapping) and _valid_source_url(source.get("url")):
                combined.setdefault(source["url"], dict(source))
    return list(combined.values())


def build_layer02_research_bindings(task: Any, gateway: Any) -> dict[str, Callable[..., Any]]:
    """Build isolated Layer 02 managers and concrete functions for one agent task.

    Manager instances are local to this task. Their in-memory indexes are compute
    state, not cross-tenant durable storage; the CEO's PostgreSQL-backed task store
    owns the durable result/evidence record.
    """
    topic = str(task.input_data.get("topic") or task.instruction).strip()
    niche = str(task.input_data.get("niche") or "general").strip()
    safe_niche = niche if niche in TopicEntry.NICHES else "general"
    trend_manager = TrendManager()
    topic_manager = TopicIntelManager()
    competitor_manager = CompetitorIntelManager()
    audience_manager = AudienceIntelManager()
    knowledge_manager = KnowledgeCollectorManager()
    verification_manager = VerificationManager()
    memory_manager = ResearchMemoryManager()
    run_scope = {
        "tenant_id": task.scope.tenant_id,
        "workspace_id": task.scope.workspace_id,
        "brand_id": task.scope.brand_id,
        "goal_id": task.goal_id,
        "task_id": task.task_id,
    }

    def trend_discovery(**context: Any) -> dict[str, Any]:
        query = f"{topic} latest trends developments {niche}"
        searched = _search(gateway, query)
        trends = []
        for item in searched["sources"]:
            entry = trend_manager.add_trend(
                keyword=item["title"],
                category=safe_niche,
                source=searched["provider"],
                description=item["snippet"],
                direction="stable",
                virality_score=0.0,
                relevance_score=0.0,
                freshness_score=0.0,
                tags=["search_candidate"],
            )
            trends.append({
                "trend_id": entry.trend_id,
                "title": item["title"],
                "source_url": item["url"],
                "snippet": item["snippet"],
                "provider": item["provider"],
            })
        return {
            "topic": topic,
            "niche": niche,
            "query": searched["query"],
            "provider": searched["provider"],
            "trends": trends,
            "sources": searched["sources"],
            "data_limitations": [
                "Search-result coverage is not a measured trend-volume or engagement metric.",
                "Trend numeric scores are intentionally not inferred from search rank.",
            ],
        }

    def topic_intelligence(**context: Any) -> dict[str, Any]:
        upstream_trends = _upstream(context, "trend_discovery")
        candidates = upstream_trends.get("trends", [])
        keywords = _keywords(" ".join(
            f"{item.get('title', '')} {item.get('snippet', '')}" for item in candidates
            if isinstance(item, Mapping)
        ))
        trend_id = candidates[0].get("trend_id", "") if candidates and isinstance(candidates[0], Mapping) else ""
        entry = topic_manager.add_topic(
            name=topic,
            niche=safe_niche,
            category=safe_niche,
            keywords=keywords,
            related_topics=[str(item.get("title", "")) for item in candidates[:8] if isinstance(item, Mapping)],
            source_trend_id=trend_id,
            confidence=0.0,
        )
        return {
            "topic": topic,
            "niche": niche,
            "topic_id": entry.topic_id,
            "keywords_from_search_titles": keywords,
            "related_topic_candidates": [str(item.get("title", "")) for item in candidates[:8] if isinstance(item, Mapping)],
            "sources": list(upstream_trends.get("sources", [])),
            "confidence_status": "not_calibrated",
        }

    def competitor_analysis(**context: Any) -> dict[str, Any]:
        searched = _search(gateway, f"{topic} competitors alternatives comparison {niche}")
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for source in searched["sources"]:
            domain = (urlparse(source["url"]).hostname or "").lower()
            if not domain:
                continue
            # Search result titles/snippets are treated as article samples, not as
            # verified competitor-account profiles or performance metrics.
            competitor_manager.content_analyzer.add_posts(
                domain,
                [ContentPost(
                    post_id=source["url"],
                    content_type="article_snippet",
                    topic=topic,
                    text=f"{source['title']} {source['snippet']}".strip(),
                    has_link=True,
                )],
            )
            grouped[domain].append(source)

        publisher_samples = []
        for domain, samples in sorted(grouped.items()):
            titles = [item["title"] for item in samples]
            publisher_samples.append({
                "domain": domain,
                "article_sample_count": len(samples),
                "topic_counts": competitor_manager.content_analyzer.analyze_topics(domain),
                "titles": titles[:5],
                "source_urls": [item["url"] for item in samples],
            })
        return {
            "topic": topic,
            "query": searched["query"],
            "provider": searched["provider"],
            "publisher_samples": publisher_samples,
            "sources": searched["sources"],
            "metrics_status": "competitor followers, post counts and engagement were not supplied by search results and are not fabricated",
        }

    def audience_research(**context: Any) -> dict[str, Any]:
        searched = _search(gateway, f"{topic} target audience needs concerns common questions {niche}")
        terms = _keywords(" ".join(
            f"{source['title']} {source['snippet']}" for source in searched["sources"]
        ))
        interest_nodes = [
            audience_manager.interest_mapper.add_interest(name=term, category=safe_niche).to_dict()
            for term in terms
        ]
        # Expose only labels and relations; InterestMapper's default numeric scores
        # are heuristic defaults, not observed audience analytics.
        signals = [
            {"term": item["name"], "category": item["category"], "related_terms": item["related"]}
            for item in interest_nodes
        ]
        return {
            "topic": topic,
            "query": searched["query"],
            "provider": searched["provider"],
            "interest_signal_candidates": signals,
            "sources": searched["sources"],
            "demographics_status": "unavailable_without a source explicitly reporting demographic data",
            "behavior_metrics_status": "unavailable_without observed platform analytics",
        }

    def knowledge_collector(**context: Any) -> dict[str, Any]:
        trend_results = _upstream(context, "trend_discovery")
        competitor_results = _upstream(context, "competitor_analysis")
        audience_results = _upstream(context, "audience_research")
        sources = _combine_sources(trend_results, competitor_results, audience_results)
        entries = []
        for source in sources:
            title = str(source.get("title") or "").strip()
            snippet = str(source.get("snippet") or "").strip()
            if not title and not snippet:
                continue
            entry = knowledge_manager.collect(
                title=title,
                content=snippet,
                source=str(source.get("provider") or "layer11_search"),
                source_url=source["url"],
                language="en",
                keywords=_keywords(f"{title} {snippet}"),
                tags=["research", "source-backed"],
                category=safe_niche,
                dedup=True,
            )
            entries.append({
                "entry_id": entry.entry_id,
                "title": entry.title,
                "content": entry.content,
                "source_url": entry.source_url,
                "keywords": list(entry.keywords),
                "is_duplicate": bool(entry.is_duplicate),
            })
        return {
            "topic": topic,
            "entry_count": len(entries),
            "entries": entries,
            "sources": [
                {
                    "url": item["source_url"],
                    "title": item["title"],
                    "snippet": item["content"],
                    "provider": "layer02_knowledge_collector",
                }
                for item in entries
            ],
            "storage_scope": "task-local working set; CEO durable task store persists final evidence",
        }

    def fact_verification(**context: Any) -> dict[str, Any]:
        knowledge = _upstream(context, "knowledge_collector")
        entries = knowledge.get("entries", [])
        if not isinstance(entries, list) or len(entries) < 2:
            return {
                "topic": topic,
                "status": "insufficient_independent_sources",
                "verified_claims": [],
                "sources": list(knowledge.get("sources", [])),
                "limitation": "At least two source records are required for cross-source comparison.",
                "review_required": True,
            }
        evidence_texts = [
            {
                "text": f"{entry.get('title', '')}. {entry.get('content', '')}".strip(),
                "source": entry.get("source_url", ""),
                "entry_id": entry.get("entry_id", ""),
            }
            for entry in entries
            if isinstance(entry, Mapping) and entry.get("source_url")
        ]
        source_text = "\n".join(
            f"{entry.get('title', '')}. {entry.get('content', '')}".strip()
            for entry in entries if isinstance(entry, Mapping)
        )
        checks = verification_manager.verify_text(source_text, evidence_texts)
        return {
            "topic": topic,
            "verification_method": "Layer 02 lexical evidence matching and contradiction heuristics",
            "verification_status": "preliminary_automated_check",
            "review_required": True,
            "checks": [item.to_dict() for item in checks],
            "sources": list(knowledge.get("sources", [])),
            "limitation": "URL syntax and lexical overlap do not establish source reachability or factual truth.",
        }

    def research_memory(**context: Any) -> dict[str, Any]:
        knowledge = _upstream(context, "knowledge_collector")
        entries = knowledge.get("entries", [])
        stored = []
        for item in entries if isinstance(entries, list) else []:
            if not isinstance(item, Mapping) or not item.get("source_url"):
                continue
            source_url = str(item["source_url"])
            entry_id = "research_" + hashlib.sha256(
                f"{task.scope.tenant_id}|{task.scope.workspace_id}|{task.scope.brand_id}|{source_url}".encode()
            ).hexdigest()[:32]
            memory_entry = memory_manager.store_entry(
                entry_id=entry_id,
                title=str(item.get("title") or ""),
                content=str(item.get("content") or ""),
                summary=str(item.get("content") or "")[:500],
                category=safe_niche,
                tags=["task-scoped", "source-backed"],
                source=source_url,
                keywords=list(item.get("keywords") or []),
                credibility_score=0.0,
                relevance_score=0.0,
                freshness_score=0.0,
            )
            memory_manager.add_citation(
                citation_id=source_url,
                source_name=urlparse(source_url).hostname or source_url,
                claim_id=entry_id,
                credibility=0.0,
            )
            stored.append({"entry_id": memory_entry.entry_id, "source_url": source_url})
        return {
            "topic": topic,
            "entries_indexed": len(stored),
            "entries": stored,
            "sources": list(knowledge.get("sources", [])),
            "storage_scope": "task-local index; durable history belongs to the CEO PostgreSQL goal/evidence ledger",
        }

    def topic_scoring(**context: Any) -> dict[str, Any]:
        knowledge = _upstream(context, "knowledge_collector")
        trend_results = _upstream(context, "trend_discovery")
        competitor_results = _upstream(context, "competitor_analysis")
        audience_results = _upstream(context, "audience_research")
        source_counts = {
            "trend_research_sources": len(trend_results.get("sources", [])),
            "competitor_research_sources": len(competitor_results.get("sources", [])),
            "audience_research_sources": len(audience_results.get("sources", [])),
            "unique_knowledge_entries": len(knowledge.get("entries", [])),
        }
        return {
            "topic": topic,
            "status": "market_score_unavailable",
            "source_coverage_counts": source_counts,
            "reason": (
                "The configured search provider supplies links, titles and snippets, "
                "not verified reach, engagement, competition or conversion metrics. "
                "No numeric market score or publish recommendation was fabricated."
            ),
            "sources": list(knowledge.get("sources", [])),
        }

    return {
        "trend_discovery": trend_discovery,
        "topic_intelligence": topic_intelligence,
        "competitor_analysis": competitor_analysis,
        "audience_research": audience_research,
        "knowledge_collector": knowledge_collector,
        "fact_verification": fact_verification,
        "research_memory": research_memory,
        "topic_scoring": topic_scoring,
    }
