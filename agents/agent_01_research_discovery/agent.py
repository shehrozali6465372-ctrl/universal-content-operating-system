"""UCOS Agent 01: Research Discovery.

This worker composes existing research components during the staged layer-to-agent migration. It does not publish content and
never treats missing account history or missing evidence as a successful check.
"""
from __future__ import annotations

import hashlib
import math
import os
import re
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

from layers.layer02_research.modules.fact_verification.verification_manager import VerificationManager
from layers.layer02_research.modules.knowledge_collector.knowledge_collector_manager import KnowledgeCollectorManager
from layers.layer02_research.modules.research_memory.research_memory_manager import ResearchMemoryManager
from layers.layer02_research.modules.research_planner.planner_manager import PlannerManager
from layers.layer02_research.modules.topic_intelligence.topic_intel_manager import TopicIntelManager
from layers.layer02_research.modules.topic_scoring.scoring_manager import ScoringManager
from layers.layer02_research.modules.trend_discovery.trend_manager import TrendManager


MAX_CANDIDATES = 20
MAX_EVIDENCE_PER_CANDIDATE = 10
MAX_CLAIMS_PER_CANDIDATE = 25
MIN_INDEPENDENT_SOURCES = 2
MIN_VERIFICATION_CONFIDENCE = 0.70
_HISTORY_COVERAGE = (
    "UCOS-managed account execution history only; posts made outside UCOS must be synced separately."
)


class ResearchDiscoveryAgent:
    """One explicit entry point for account-scoped research decisions.

    Args:
        account_id: Required registered UCOS account. Every history read and
            agent-owned state directory is scoped to this account.
        account_resolver: Optional callable(account_id) -> account-like object.
            The default resolves the account through UCOS AccountRegistry.
        history_reader: Optional callable(account_id) -> list[dict]. The default
            reads the account's own content.execution_history collection.
        candidate_provider: Optional callable(account_id, niche, limit) -> candidates.
            Without it, candidates come only from this account's stored topics
            and configured TrendManager sources.
        evidence_provider: Optional callable(topic, niche, limit) -> evidence records.
            It must return source-backed evidence; the agent never fabricates sources.
        result_writer: Optional callable(report). The default appends the report
            to the account-local memory store.
        storage_root: Optional durable root for Layer 02 manager state. Account IDs
            are hashed before becoming directory names. If omitted, the registered
            account workspace is used when the default AccountRegistry is active.
        trend_sources: Optional mapping of source name to real fetch callback.
        components: Optional dependency overrides for tests/application wiring.
            Keys: trend_manager, topic_manager, knowledge_manager, verifier,
            memory_manager, scoring_manager, planner_manager.

    Candidate records accept: topic/name/title, optional evidence list, optional
    claims list, optional scores mapping, and optional draft_text. Each evidence
    record needs a source and content/text/snippet. URLs are retained only when
    they are valid HTTP(S) URLs.

    A READY_FOR_WRITING_REVIEW result is a hand-off to the next UCOS stage, not
    permission to publish. The publication pipeline retains its own gates.
    """

    name = "research_agent"
    version = "1.0.0"

    def __init__(
        self,
        account_id: str,
        *,
        account_resolver: Callable[[str], Any] | None = None,
        history_reader: Callable[[str], Any] | None = None,
        candidate_provider: Callable[[str, str, int], Sequence[Any]] | None = None,
        evidence_provider: Callable[[str, str, int], Sequence[Mapping[str, Any]]] | None = None,
        result_writer: Callable[[dict[str, Any]], Any] | None = None,
        storage_root: str | os.PathLike[str] | None = None,
        trend_sources: Mapping[str, Callable[..., Any]] | None = None,
        components: Mapping[str, Any] | None = None,
    ) -> None:
        self.account_id = str(account_id or "").strip()
        if not self.account_id:
            raise ValueError("account_id is required")

        self._registry = None
        self._account_resolver = account_resolver
        self._history_reader = history_reader
        self._candidate_provider = candidate_provider
        self._evidence_provider = evidence_provider
        self._result_writer = result_writer
        self._components_override = dict(components or {})

        account = self._resolve_account()
        if not bool(self._field(account, "enabled", True)):
            raise LookupError("account is disabled")
        resolved_account_id = str(self._field(account, "account_id", self.account_id) or "").strip()
        if resolved_account_id != self.account_id:
            raise ValueError("account_resolver returned a different account_id")

        self.platform = str(self._field(account, "platform", "") or "").strip().lower()
        self.niche = str(self._field(account, "niche", "") or "").strip()
        if not self.platform or not self.niche:
            raise ValueError("registered account must include platform and niche")

        self._storage_dir = self._resolve_storage_dir(storage_root)
        if self._storage_dir is not None:
            self._storage_dir.mkdir(parents=True, exist_ok=True)

        override = self._components_override
        self.trend_manager = override.get("trend_manager") or TrendManager(
            self._path("trends.json")
        )
        self.topic_manager = override.get("topic_manager") or TopicIntelManager(
            self._path("topics.json")
        )
        self.knowledge_manager = override.get("knowledge_manager") or KnowledgeCollectorManager(
            self._path("knowledge.json")
        )
        self.verifier = override.get("verifier") or VerificationManager(
            self._path("verification.json")
        )
        self.memory_manager = override.get("memory_manager") or ResearchMemoryManager(
            self._path("research-memory.json")
        )
        self.scoring_manager = override.get("scoring_manager") or ScoringManager(
            self._path("topic-scores.json")
        )
        self.planner_manager = override.get("planner_manager") or PlannerManager()

        for source_name, fetch_fn in (trend_sources or {}).items():
            if callable(fetch_fn):
                self.trend_manager.register_source(str(source_name), fetch_fn=fetch_fn)

    @staticmethod
    def _field(obj: Any, name: str, default: Any = None) -> Any:
        if isinstance(obj, Mapping):
            return obj.get(name, default)
        return getattr(obj, name, default)

    def _get_registry(self) -> Any:
        if self._registry is None:
            from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry

            self._registry = AccountRegistry()
        return self._registry

    def _resolve_account(self) -> Any:
        if self._account_resolver is not None:
            account = self._account_resolver(self.account_id)
        else:
            account = self._get_registry().get(self.account_id)
        if account is None:
            raise LookupError("unknown account_id")
        return account

    def _resolve_storage_dir(
        self, storage_root: str | os.PathLike[str] | None
    ) -> Path | None:
        """Use local state only outside production; production state belongs in Neon."""
        production = os.environ.get("APP_ENV", "development").strip().lower() in {"production", "prod"}
        if production:
            if storage_root is not None:
                raise ValueError("storage_root is disabled in production; use L13 PostgreSQL/Neon")
            return None
        configured_root = storage_root or os.environ.get("UCOS_RESEARCH_AGENT_DATA_DIR")
        if configured_root:
            account_key = hashlib.sha256(self.account_id.encode("utf-8")).hexdigest()[:24]
            return Path(configured_root).expanduser() / account_key
        if self._account_resolver is None:
            return self._get_registry().workspace_path(self.account_id) / "research_agent"
        return None

    def _path(self, filename: str) -> str | None:
        return str(self._storage_dir / filename) if self._storage_dir is not None else None

    def _has_durable_storage(self) -> bool:
        """Fail closed unless a durable result store or explicit writer is available."""
        if self._result_writer is not None or self._storage_dir is not None:
            return True
        production = os.environ.get("APP_ENV", "development").strip().lower() in {"production", "prod"}
        if not production:
            return False
        try:
            from layers.layer07_publishing.modules.account_control.account_data_store import AccountDataStore
            AccountDataStore(registry=self._get_registry()).get(
                self.account_id, "memory", "collection:research_agent_runs", default=[]
            )
            return True
        except Exception:
            return False
self, filename: str) -> str | None:
        return str(self._storage_dir / filename) if self._storage_dir is not None else None

    def _load_history(self) -> tuple[list[dict[str, Any]], bool, str | None]:
        try:
            if self._history_reader is not None:
                rows = self._history_reader(self.account_id)
            else:
                from layers.layer07_publishing.modules.account_control.account_data_store import AccountDataStore

                store = AccountDataStore(registry=self._get_registry())
                production = os.environ.get("APP_ENV", "development").strip().lower() in {"production", "prod"}
                if production:
                    baseline = store.bootstrap_legacy_store(self.account_id, "content")
                    if baseline.get("status") != "complete":
                        return [], False, "history_baseline_not_verified"
                rows = store.get(
                    self.account_id, "content", "collection:execution_history", default=[]
                )
            if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
                return [], False, "invalid_history_shape"
            return [dict(row) for row in rows], True, None
        except Exception:
            # Do not expose database paths, SQL, or provider errors in the report.
            return [], False, "history_reader_failed"

    def _discover_candidates(self, limit: int) -> list[Any]:
        if self._candidate_provider is not None:
            values = self._candidate_provider(self.account_id, self.niche, limit)
            return list(values or [])[:limit]

        found: list[Any] = []
        try:
            self.trend_manager.discover(category=self.niche)
            for item in self.trend_manager.top_trends(category=self.niche, limit=limit):
                row = dict(item)
                row.setdefault("topic", row.get("keyword") or row.get("name") or row.get("title"))
                found.append(row)
        except Exception:
            pass
        try:
            for item in self.topic_manager.get_top_topics(count=limit, niche=self.niche):
                row = self._as_dict(item)
                row.setdefault("topic", row.get("name") or row.get("title"))
                found.append(row)
        except Exception:
            pass
        return found[:limit]

    @staticmethod
    def _as_dict(value: Any) -> dict[str, Any]:
        if isinstance(value, Mapping):
            return dict(value)
        method = getattr(value, "to_dict", None)
        if callable(method):
            result = method()
            return dict(result) if isinstance(result, Mapping) else {}
        if hasattr(value, "__dict__"):
            return dict(vars(value))
        return {}

    @staticmethod
    def _normalized(value: Any) -> str:
        text = str(value or "").strip().casefold()
        text = re.sub(r"https?://\S+|www\.\S+", " ", text)
        text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _safe_url(value: Any) -> str:
        raw = str(value or "").strip()
        if not raw or len(raw) > 2048:
            return ""
        try:
            parts = urlsplit(raw)
            if parts.scheme.lower() in {"http", "https"} and parts.hostname:
                return raw
        except ValueError:
            pass
        return ""

    def _normalize_evidence(self, values: Any) -> list[dict[str, str]]:
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            return []
        normalized: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in list(values)[:MAX_EVIDENCE_PER_CANDIDATE]:
            if not isinstance(item, Mapping):
                continue
            source = str(item.get("source") or item.get("source_name") or item.get("publisher") or "").strip()[:200]
            title = str(item.get("title") or item.get("name") or "").strip()[:300]
            content = str(item.get("content") or item.get("text") or item.get("snippet") or "").strip()
            content = content[:20000]
            url = self._safe_url(item.get("url") or item.get("source_url"))
            if not source or not content:
                continue
            source_key = self._source_key(source, url)
            if source_key in seen:
                continue
            seen.add(source_key)
            normalized.append({"source": source, "title": title, "content": content, "url": url})
        return normalized

    @staticmethod
    def _source_key(source: str, url: str) -> str:
        if url:
            host = (urlsplit(url).hostname or "").lower()
            if host.startswith("www."):
                host = host[4:]
            if host:
                return host
        return re.sub(r"\s+", " ", source.casefold()).strip()

    def _match_history(
        self, topic: str, draft_text: str, history: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        target_topic = self._normalized(topic)
        target_text = self._normalized(draft_text)
        for row in history:
            past_topic = self._normalized(row.get("topic") or row.get("title") or "")
            past_text = self._normalized(row.get("text") or row.get("content") or "")
            match_type = ""
            if target_text and past_text and target_text == past_text:
                match_type = "exact_content"
            elif target_topic and past_topic and target_topic == past_topic:
                match_type = "exact_topic"
            elif target_topic and past_topic:
                ratio = SequenceMatcher(None, target_topic, past_topic).ratio()
                target_tokens = set(target_topic.split())
                past_tokens = set(past_topic.split())
                union = target_tokens | past_tokens
                jaccard = len(target_tokens & past_tokens) / len(union) if union else 0.0
                if min(len(target_tokens), len(past_tokens)) >= 3 and (ratio >= 0.92 or jaccard >= 0.85):
                    match_type = "possible_topic"
            if match_type:
                published = row.get("published")
                if isinstance(published, str):
                    if published.strip().lower() in {"true", "1", "yes", "published"}:
                        published = True
                    elif published.strip().lower() in {"false", "0", "no", "draft", "failed"}:
                        published = False
                    else:
                        published = None
                elif not isinstance(published, bool):
                    published = None
                return {
                    "match_type": match_type,
                    "published": published,
                    "matched_topic": str(row.get("topic") or row.get("title") or "")[:200],
                    "post_id_present": bool(row.get("post_id")),
                }
        return None

    def _collect_evidence(
        self, topic: str, evidence: list[dict[str, str]], run_id: str, index: int
    ) -> tuple[bool, list[str]]:
        warnings: list[str] = []
        for evidence_index, item in enumerate(evidence, 1):
            try:
                self.knowledge_manager.collect(
                    title=item["title"] or topic[:300],
                    content=item["content"],
                    source=item["source"],
                    source_url=item["url"],
                    category=self.niche,
                    keywords=[topic],
                    tags=["research-agent", self.platform],
                    clean=True,
                    extract_metadata=True,
                    dedup=True,
                )
            except Exception:
                warnings.append("knowledge_store_failed")
        return not warnings, sorted(set(warnings))

    def _verify_claims(
        self, candidate: Mapping[str, Any], evidence: list[dict[str, str]]
    ) -> list[dict[str, Any]]:
        claims_raw = candidate.get("claims") or []
        if isinstance(claims_raw, str):
            claims_raw = [claims_raw]
        if not isinstance(claims_raw, Sequence) or isinstance(claims_raw, (bytes, str)):
            return []
        evidence_texts = [
            {"source": item["source"], "text": item["content"]}
            for item in evidence
        ]
        results: list[dict[str, Any]] = []
        for raw_claim in list(claims_raw)[:MAX_CLAIMS_PER_CANDIDATE]:
            claim = str(raw_claim.get("claim") or raw_claim.get("text") or "") if isinstance(raw_claim, Mapping) else str(raw_claim or "")
            claim = claim.strip()[:2000]
            if not claim:
                continue
            try:
                value = self.verifier.verify_claim(claim, evidence_texts)
                status = str(getattr(value, "status", "") or self._as_dict(value).get("status") or "unknown").casefold()
                confidence_result = getattr(value, "confidence_result", None)
                confidence = getattr(confidence_result, "confidence", getattr(value, "confidence", 0.0))
                try:
                    confidence = float(confidence)
                    if not math.isfinite(confidence):
                        confidence = 0.0
                    confidence = max(0.0, min(1.0, confidence))
                except (TypeError, ValueError):
                    confidence = 0.0
                results.append({"claim": claim, "status": status, "confidence": round(confidence, 4)})
            except Exception:
                results.append({"claim": claim, "status": "verification_error", "confidence": 0.0})
        return results

    def _store_topic(self, topic: str, candidate: Mapping[str, Any], confidence: float) -> tuple[bool, str | None]:
        scores = candidate.get("scores") if isinstance(candidate.get("scores"), Mapping) else {}
        numeric = {}
        for key, value in scores.items():
            try:
                number = float(value)
                if math.isfinite(number):
                    numeric[str(key)] = max(0.0, min(10.0, number))
            except (TypeError, ValueError):
                continue
        try:
            existing = self.topic_manager.get_topic_by_name(topic)
            if existing is None:
                self.topic_manager.add_topic(
                    name=topic,
                    niche=self.niche,
                    category=str(candidate.get("category") or self.niche),
                    engagement_score=numeric.get("engagement_score", 0.0),
                    audience_fit_score=numeric.get("audience_fit_score", 0.0),
                    competition_score=numeric.get("competition_score", 0.0),
                    keywords=[str(k) for k in candidate.get("keywords", [])[:20]] if isinstance(candidate.get("keywords", []), list) else [],
                    confidence=confidence,
                    auto_categorize=True,
                )
            return True, None
        except Exception:
            return False, "topic_store_failed"

    def _score_topic(self, topic: str, candidate: Mapping[str, Any], evidence: list[dict[str, str]]) -> dict[str, Any]:
        scores = candidate.get("scores") if isinstance(candidate.get("scores"), Mapping) else {}
        sanitized = {}
        for key, value in scores.items():
            try:
                number = float(value)
                if math.isfinite(number):
                    sanitized[str(key)] = max(0.0, min(10.0, number))
            except (TypeError, ValueError):
                continue
        refs = [item["url"] or item["source"] for item in evidence]
        result = self.scoring_manager.score_topic(topic, niche=self.niche, scores=sanitized, evidence=refs)
        data = self._as_dict(result)
        if not data:
            data = {
                "topic": str(getattr(result, "topic", topic)),
                "niche": str(getattr(result, "niche", self.niche)),
                "overall_score": float(getattr(result, "overall_score", 0.0) or 0.0),
                "recommendation": str(getattr(result, "recommendation", "unknown")),
                "confidence": float(getattr(result, "confidence", 0.0) or 0.0),
                "raw_scores": getattr(result, "raw_scores", {}),
                "weighted_scores": getattr(result, "weighted_scores", {}),
            }
        data["score_inputs_supplied"] = bool(sanitized)
        data["evidence_sources"] = len(refs)
        return data

    def _plan_summary(self, topic: str) -> dict[str, Any] | None:
        try:
            plan = self.planner_manager.create_plan(topic=topic, niche=self.niche)
            tasks = getattr(plan, "tasks", []) or []
            return {
                "plan_id": str(getattr(plan, "plan_id", "")),
                "status": str(getattr(plan, "status", "ready")),
                "task_count": len(tasks),
                "execution_started": False,
            }
        except Exception:
            return None

    def _persist_report(self, report: dict[str, Any]) -> None:
        payload = dict(report)
        payload.pop("persistence", None)
        if self._result_writer is not None:
            self._result_writer(payload)
            return
        from layers.layer07_publishing.modules.account_control.account_data_store import AccountDataStore

        AccountDataStore(registry=self._get_registry()).append(
            self.account_id, "memory", "research_agent_runs", payload
        )

    def run(
        self,
        candidates: Sequence[Any] | None = None,
        *,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Research candidates and return a conservative, JSON-serializable report.

        No candidate is marked ready unless account history is readable, agent
        state has an account-scoped durable path, at least two independent source
        hosts/names support the topic, all supplied claims verify above threshold,
        and required state/planning steps succeeded.
        """
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        limit = min(limit, MAX_CANDIDATES)
        run_id = str(uuid4())
        started = datetime.now(timezone.utc).isoformat()
        history, history_available, history_error = self._load_history()
        history_summary = {
            "status": "available" if history_available else "unknown",
            "records_checked": len(history) if history_available else 0,
            "coverage": _HISTORY_COVERAGE,
            "error_code": history_error,
        }

        warnings: list[str] = []
        try:
            candidate_values = list(candidates)[:limit] if candidates is not None else self._discover_candidates(limit)
        except Exception:
            candidate_values = []
            warnings.append("candidate_provider_failed")

        results: list[dict[str, Any]] = []
        seen_in_batch: set[str] = set()
        for index, raw in enumerate(candidate_values, 1):
            candidate = self._as_dict(raw) if not isinstance(raw, str) else {"topic": raw}
            topic = str(candidate.get("topic") or candidate.get("name") or candidate.get("title") or candidate.get("keyword") or "").strip()[:500]
            if not topic:
                results.append({
                    "topic": "",
                    "decision": "REJECT_INVALID_CANDIDATE",
                    "reason_codes": ["topic_missing"],
                })
                continue

            normalized_topic = self._normalized(topic)
            if normalized_topic in seen_in_batch:
                results.append({
                    "topic": topic,
                    "decision": "BLOCK_DUPLICATE_IN_BATCH",
                    "reason_codes": ["candidate_batch_repeat"],
                    "duplicate": {"match_type": "exact_topic_in_batch"},
                })
                continue
            seen_in_batch.add(normalized_topic)

            evidence_raw = candidate.get("evidence") or []
            evidence = self._normalize_evidence(evidence_raw)
            if not evidence and self._evidence_provider is not None:
                try:
                    evidence = self._normalize_evidence(
                        self._evidence_provider(topic, self.niche, MAX_EVIDENCE_PER_CANDIDATE)
                    )
                except Exception:
                    warnings.append("evidence_provider_failed")

            history_match = self._match_history(
                topic, str(candidate.get("draft_text") or "")[:20000], history
            ) if history_available else None

            claims = self._verify_claims(candidate, evidence)
            valid_claims = len(claims)
            contradicted = any(
                item["status"] in {"contradicted", "contradiction", "false", "unsupported", "verification_error"}
                for item in claims
            )
            all_verified = bool(claims) and all(
                item["status"] == "verified" and item["confidence"] >= MIN_VERIFICATION_CONFIDENCE
                for item in claims
            )
            verified_confidence = (
                min((item["confidence"] for item in claims), default=0.0) if all_verified else 0.0
            )

            score: dict[str, Any]
            try:
                score = self._score_topic(topic, candidate, evidence)
            except Exception:
                score = {"topic": topic, "score_inputs_supplied": False, "error_code": "scoring_failed"}
                warnings.append("scoring_failed")

            topic_stored, topic_error = self._store_topic(topic, candidate, verified_confidence)
            if topic_error:
                warnings.append(topic_error)

            knowledge_stored, knowledge_warnings = self._collect_evidence(topic, evidence, run_id, index)
            warnings.extend(knowledge_warnings)

            memory_stored = True
            try:
                joined_evidence = "\n\n".join(
                    f"Source: {item['source']}\nURL: {item['url']}\n{item['content']}"
                    for item in evidence
                )
                digest = hashlib.sha256(f"{self.account_id}|{run_id}|{topic}".encode("utf-8")).hexdigest()[:24]
                self.memory_manager.store_entry(
                    entry_id=f"{run_id}-{digest}",
                    title=topic,
                    content=joined_evidence or str(candidate.get("description") or ""),
                    summary=f"Research candidate for niche {self.niche}; decision pending.",
                    category=self.niche,
                    tags=["research-agent", self.platform],
                    source="; ".join(item["source"] for item in evidence),
                    keywords=[topic],
                )
            except Exception:
                memory_stored = False
                warnings.append("research_memory_store_failed")

            plan = self._plan_summary(topic)
            duplicate = history_match
            reason_codes: list[str] = []
            if not self._has_durable_storage():
                decision = "HOLD_RESEARCH_STORAGE_UNAVAILABLE"
                reason_codes.append("account_scoped_storage_not_configured")
            elif not history_available:
                decision = "HOLD_HISTORY_UNAVAILABLE"
                reason_codes.append(history_error or "history_unknown")
            elif duplicate and duplicate["published"] is True:
                decision = "BLOCK_DUPLICATE_PUBLISHED"
                reason_codes.append(duplicate["match_type"])
            elif duplicate and duplicate["published"] is False:
                decision = "HOLD_PRIOR_GENERATION_REVIEW"
                reason_codes.append("topic_or_content_seen_in_prior_ucos_run")
            elif duplicate:
                decision = "HOLD_HISTORY_MATCH_STATUS_UNKNOWN"
                reason_codes.append("matched_history_record_has_unknown_publish_status")
            elif not topic_stored or not knowledge_stored or not memory_stored:
                decision = "HOLD_RESEARCH_STATE_PERSISTENCE_FAILED"
                reason_codes.append("research_state_persistence_failed")
            elif plan is None:
                decision = "HOLD_RESEARCH_PLAN_FAILED"
                reason_codes.append("research_plan_not_created")
            elif len(evidence) < MIN_INDEPENDENT_SOURCES:
                decision = "NEEDS_MORE_EVIDENCE"
                reason_codes.append("fewer_than_two_independent_sources")
            elif valid_claims == 0:
                decision = "NEEDS_CLAIM_VERIFICATION"
                reason_codes.append("no_claims_supplied_for_verification")
            elif contradicted:
                decision = "BLOCK_CONTRADICTED_CLAIM"
                reason_codes.append("one_or_more_claims_contradicted_or_verification_failed")
            elif not all_verified:
                decision = "HUMAN_REVIEW_REQUIRED"
                reason_codes.append("all_claims_not_verified_at_required_confidence")
            else:
                decision = "READY_FOR_WRITING_REVIEW"
                reason_codes.append("history_clear_evidence_and_claim_checks_passed")

            results.append({
                "topic": topic,
                "platform": self.platform,
                "niche": self.niche,
                "decision": decision,
                "reason_codes": reason_codes,
                "duplicate": duplicate or {"match_type": "no_match", "published": False},
                "evidence": [
                    {"source": item["source"], "title": item["title"], "url": item["url"]}
                    for item in evidence
                ],
                "evidence_count": len(evidence),
                "independent_source_count": len({self._source_key(item["source"], item["url"]) for item in evidence}),
                "verification": {
                    "status": (
                        "verified" if all_verified else
                        "contradicted_or_failed" if contradicted else
                        "needs_review" if claims else "not_run"
                    ),
                    "claims_checked": valid_claims,
                    "minimum_confidence": verified_confidence,
                    "results": claims,
                },
                "score": score,
                "research_plan": plan,
                "persistence": {
                    "topic_state": "saved" if topic_stored else "failed",
                    "knowledge_state": "saved" if knowledge_stored else "failed",
                    "research_memory": "saved" if memory_stored else "failed",
                },
            })

        report: dict[str, Any] = {
            "agent": self.name,
            "agent_version": self.version,
            "run_id": run_id,
            "account_id": self.account_id,
            "platform": self.platform,
            "niche": self.niche,
            "started_at": started,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "status": "completed" if results else "no_candidates",
            "history": history_summary,
            "history_coverage": _HISTORY_COVERAGE,
            "candidate_count": len(results),
            "candidates": results,
            "recommended_topic": next(
                (item["topic"] for item in results if item.get("decision") == "READY_FOR_WRITING_REVIEW"),
                None,
            ),
            "publishing": {"performed": False, "status": "not_requested"},
            "warnings": sorted(set(warnings)),
            "persistence": {"status": "pending"},
        }
        try:
            self._persist_report(report)
            report["persistence"] = {"status": "persisted"}
        except Exception:
            report["persistence"] = {"status": "failed", "error_code": "result_writer_failed"}
            report["warnings"] = sorted(set(report["warnings"] + ["result_writer_failed"]))
            for item in report["candidates"]:
                if item.get("decision") == "READY_FOR_WRITING_REVIEW":
                    item["decision"] = "HOLD_PERSISTENCE_UNAVAILABLE"
                    item["reason_codes"] = list(item["reason_codes"]) + ["research_report_not_persisted"]
            report["recommended_topic"] = None
            report["status"] = "blocked_persistence"
        if report["status"] == "completed" and not report["recommended_topic"]:
            report["status"] = "completed_with_holds"
        return report
