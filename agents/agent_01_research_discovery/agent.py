"""UCOS Agent 01: Research Discovery.

Owns one bounded responsibility: discover candidate topics, collect attributable
web evidence, check the target account's known publication history, and store a
research evidence pack for the next worker. Fact verification, scoring, writing,
and publishing belong to separate agents and are not performed here.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4


MAX_CANDIDATES = 20
MAX_EVIDENCE_PER_CANDIDATE = 10
MIN_INDEPENDENT_SOURCES = 2
_HISTORY_COVERAGE = (
    "UCOS-managed account history only; posts outside UCOS are included only after a verified import."
)


class ResearchDiscoveryAgent:
    """Agent 01: gather research inputs and enforce account-local duplicate holds.

    The worker has no imports from legacy Layer 02 research modules. Its only
    built-in network source is the optional Tavily adapter; identity and durable
    account state use UCOS's shared account-registry/data-store boundary.

    Args:
        account_id: Required registered, enabled UCOS account.
        account_resolver: Optional callable(account_id) -> account-like object.
        history_reader: Optional callable(account_id) -> list[dict], for isolated
            tests or an explicitly wired history repository.
        candidate_provider: Optional callable(account_id, niche, limit) -> sequence
            of candidate mappings. Defaults to Tavily when TAVILY_API_KEY is set.
        evidence_provider: Optional callable(topic, niche, limit) -> source records.
            Defaults to Tavily when TAVILY_API_KEY is set.
        result_writer: Optional durable report writer. Candidate evidence still
            requires account_store or the local development state directory.
        account_store: Optional account-scoped persistence facade override.
        storage_root: Development/test state root only; forbidden in production.

    Candidate records accept topic/name/title, optional evidence records, optional
    draft_text, optional claims for the next agent, and optional source_relevance_score.
    Evidence records require a source label, content/snippet, and a valid HTTP(S) URL.

    READY_FOR_VERIFICATION means the topic/evidence pack may be handed to Agent 06.
    It is neither a factual-verification result nor publish authorization.
    """

    name = "research_discovery"
    agent_id = "AG01"
    version = "1.1.0"

    def __init__(
        self,
        account_id: str,
        *,
        account_resolver: Callable[[str], Any] | None = None,
        history_reader: Callable[[str], Any] | None = None,
        candidate_provider: Callable[[str, str, int], Sequence[Any]] | None = None,
        evidence_provider: Callable[[str, str, int], Sequence[Mapping[str, Any]]] | None = None,
        result_writer: Callable[[dict[str, Any]], Any] | None = None,
        account_store: Any | None = None,
        storage_root: str | os.PathLike[str] | None = None,
    ) -> None:
        self.account_id = str(account_id or "").strip()
        if not self.account_id:
            raise ValueError("account_id is required")

        # Dependency overrides are for isolated unit tests only. Production must
        # resolve the real registered account, real Tavily provider and real Neon
        # store; a caller must not be able to certify it using fake dependencies.
        if self._is_production():
            injected = [
                name for name, value in (
                    ("account_resolver", account_resolver),
                    ("history_reader", history_reader),
                    ("candidate_provider", candidate_provider),
                    ("evidence_provider", evidence_provider),
                    ("result_writer", result_writer),
                    ("account_store", account_store),
                ) if value is not None
            ]
            if injected:
                raise ValueError(
                    "production mode forbids injected test dependencies: " + ", ".join(injected)
                )

        self._registry = None
        self._account_resolver = account_resolver
        self._history_reader = history_reader
        self._candidate_provider = candidate_provider
        self._evidence_provider = evidence_provider
        self._result_writer = result_writer
        self._account_store_override = account_store
        self._source = None

        if self._candidate_provider is None and os.environ.get("TAVILY_API_KEY", "").strip():
            from agents.agent_01_research_discovery.tavily_source import TavilyResearchSource

            self._source = TavilyResearchSource.from_env()
        elif self._candidate_provider is None and self._is_production():
            # Unit tests and development remain offline by default. The keyless
            # public provider is selected only for a real production run.
            from agents.agent_01_research_discovery.gdelt_context_source import GDELTContextResearchSource

            self._source = GDELTContextResearchSource()
        if self._source is not None and self._candidate_provider is None:
            self._candidate_provider = self._source.discover_candidates
            if self._evidence_provider is None:
                self._evidence_provider = self._source.fetch_evidence

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

        self._source_status: dict[str, Any] = {
            "status": "configured" if self._candidate_provider is not None else "unconfigured",
            "provider": getattr(self._source, "name", None) if self._source is not None else (
                "injected" if self._candidate_provider is not None else None
            ),
            "candidate_provider_configured": self._candidate_provider is not None,
            "evidence_provider_configured": self._evidence_provider is not None,
            "tavily_configured_from_environment": bool(os.environ.get("TAVILY_API_KEY", "").strip()),
            "gdelt_fallback_available": self._source is not None and getattr(self._source, "name", "") == "gdelt_context",
        }

    @staticmethod
    def _field(obj: Any, name: str, default: Any = None) -> Any:
        if isinstance(obj, Mapping):
            return obj.get(name, default)
        return getattr(obj, name, default)

    @staticmethod
    def _is_production() -> bool:
        return os.environ.get("APP_ENV", "development").strip().lower() in {"production", "prod"}

    def _get_registry(self) -> Any:
        if self._registry is None:
            from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry

            self._registry = AccountRegistry()
        return self._registry

    def _resolve_account(self) -> Any:
        account = (
            self._account_resolver(self.account_id)
            if self._account_resolver is not None
            else self._get_registry().get(self.account_id)
        )
        if account is None:
            raise LookupError("unknown account_id")
        return account

    def _resolve_storage_dir(
        self, storage_root: str | os.PathLike[str] | None
    ) -> Path | None:
        if self._is_production():
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

    def _account_data_store(self) -> Any:
        if self._account_store_override is not None:
            return self._account_store_override
        from layers.layer07_publishing.modules.account_control.account_data_store import AccountDataStore

        return AccountDataStore(registry=self._get_registry())

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

    @staticmethod
    def _source_key(source: str, url: str) -> str:
        if url:
            host = (urlsplit(url).hostname or "").lower()
            if host.startswith("www."):
                host = host[4:]
            if host:
                return host
        return re.sub(r"\s+", " ", source.casefold()).strip()

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
            content = str(item.get("content") or item.get("text") or item.get("snippet") or "").strip()[:20000]
            url = self._safe_url(item.get("url") or item.get("source_url"))
            if not source or not title or not content or not url:
                continue
            source_key = self._source_key(source, url)
            if source_key in seen:
                continue
            seen.add(source_key)
            normalized.append({
                "source": source,
                "title": title,
                "content": content,
                "url": url,
                "published_at": str(item.get("published_at") or item.get("published_date") or "")[:64],
            })
        return normalized

    def _load_history(self) -> tuple[list[dict[str, Any]], bool, str | None]:
        try:
            if self._history_reader is not None:
                rows = self._history_reader(self.account_id)
            else:
                store = self._account_data_store()
                if self._is_production():
                    if hasattr(store, "bootstrap_legacy_store"):
                        baseline = store.bootstrap_legacy_store(self.account_id, "content")
                    else:
                        baseline = store.get(
                            self.account_id, "memory", "history_baseline:content:v1", default=None
                        )
                    from layers.layer07_publishing.modules.account_control.account_data_store import (
                        is_verified_history_baseline,
                    )
                    if not is_verified_history_baseline(baseline):
                        return [], False, "history_baseline_not_verified"
                rows = store.get(
                    self.account_id, "content", "collection:execution_history", default=[]
                )
            if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
                return [], False, "invalid_history_shape"
            return [dict(row) for row in rows], True, None
        except Exception:
            return [], False, "history_reader_failed"

    def _discover_candidates(self, limit: int) -> list[Any]:
        if self._candidate_provider is None:
            self._source_status = {
                **self._source_status,
                "status": "unconfigured",
                "error_code": "research_provider_not_configured",
            }
            return []
        try:
            candidates = self._candidate_provider(self.account_id, self.niche, limit)
            self._source_status = {
                **self._source_status,
                "status": "configured",
            }
            return list(candidates or [])[:limit]
        except Exception:
            self._source_status = {
                **self._source_status,
                "status": "unavailable",
                "error_code": "candidate_provider_failed",
            }
            return []

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

    def _has_durable_storage(self) -> bool:
        if self._account_store_override is not None or self._storage_dir is not None:
            return True
        if not self._is_production():
            return False
        try:
            self._account_data_store().get(
                self.account_id, "memory", "research_agent_storage_probe", default=None
            )
            return True
        except Exception:
            return False

    def _write_state(self, key: str, payload: dict[str, Any]) -> None:
        if self._account_store_override is not None or self._is_production():
            self._account_data_store().put(self.account_id, "memory", key, payload)
            return
        if self._storage_dir is None:
            raise RuntimeError("account-scoped local state is not configured")
        safe_name = hashlib.sha256(key.encode("utf-8")).hexdigest()
        target = self._storage_dir / f"{safe_name}.json"
        fd, temp_name = tempfile.mkstemp(prefix=f".{safe_name}.", suffix=".tmp", dir=str(self._storage_dir))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, sort_keys=True, default=str)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, target)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def _persist_candidate(
        self, run_id: str, candidate_key: str, topic: str,
        candidate: Mapping[str, Any], evidence: list[dict[str, str]],
    ) -> None:
        for index, item in enumerate(evidence, 1):
            self._write_state(
                f"research_evidence:{candidate_key}:{index}",
                {
                    "run_id": run_id,
                    "topic": topic,
                    "niche": self.niche,
                    "platform": self.platform,
                    **item,
                },
            )
        self._write_state(
            f"research_candidate:{candidate_key}",
            {
                "run_id": run_id,
                "topic": topic,
                "niche": self.niche,
                "platform": self.platform,
                "decision": "READY_FOR_VERIFICATION",
                "source_relevance_score": candidate.get("source_relevance_score"),
                "source_relevance_metric": "vendor_search_relevance_not_content_performance",
                "evidence": [
                    {"source": item["source"], "title": item["title"], "url": item["url"]}
                    for item in evidence
                ],
                "claims_for_agent_06": candidate.get("claims") or [],
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    def _persist_report(self, report: dict[str, Any]) -> None:
        payload = dict(report)
        if self._result_writer is not None:
            self._result_writer(payload)
            return
        self._write_state(f"research_agent_run:{payload['run_id']}", payload)

    def run(
        self,
        candidates: Sequence[Any] | None = None,
        *,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Create a JSON evidence-pack report without verifying claims or publishing."""
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        if self._is_production() and candidates is not None:
            raise ValueError("production mode does not accept caller-supplied candidates")
        if self._is_production() and (
            self._source is None
            or self._source_status.get("provider") not in {"tavily", "gdelt_context"}
        ):
            raise RuntimeError("production mode requires an approved real research provider")
        requested_limit = min(limit, MAX_CANDIDATES)
        limit = requested_limit
        if self._source is not None:
            limit = min(limit, self._source.max_candidates_per_run)

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

        # Do not spend the real provider's API quota or gather topics until
        # production account-history coverage is independently verified.
        if self._is_production() and not history_available:
            blocked_report: dict[str, Any] = {
                "agent": self.name,
                "agent_id": self.agent_id,
                "agent_version": self.version,
                "run_id": run_id,
                "account_id": self.account_id,
                "platform": self.platform,
                "niche": self.niche,
                "started_at": started,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "status": "blocked_history_unavailable",
                "research_sources": dict(self._source_status),
                "history": history_summary,
                "history_coverage": _HISTORY_COVERAGE,
                "candidate_count": 0,
                "requested_candidate_limit": min(limit, MAX_CANDIDATES),
                "effective_candidate_limit": limit,
                "candidates": [],
                "recommended_topic": None,
                "publishing": {"performed": False, "status": "not_requested"},
                "warnings": [history_error or "history_unknown"],
                "persistence": {"status": "pending"},
            }
            try:
                self._persist_report(blocked_report)
                blocked_report["persistence"] = {"status": "persisted"}
            except Exception:
                blocked_report["persistence"] = {"status": "failed", "error_code": "result_writer_failed"}
            return blocked_report

        if candidates is not None:
            self._source_status = {
                **self._source_status,
                "status": "caller_supplied",
                "mode": "explicit_candidates",
            }
            candidate_values = list(candidates)[:limit]
        else:
            candidate_values = self._discover_candidates(limit)

        results: list[dict[str, Any]] = []
        seen_in_batch: set[str] = set()
        for index, raw in enumerate(candidate_values, 1):
            candidate = dict(raw) if isinstance(raw, Mapping) else (
                {"topic": raw} if isinstance(raw, str) else {}
            )
            topic = str(candidate.get("topic") or candidate.get("name") or candidate.get("title") or "").strip()[:500]
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

            if not history_available:
                results.append({
                    "topic": topic,
                    "platform": self.platform,
                    "niche": self.niche,
                    "decision": "HOLD_HISTORY_UNAVAILABLE",
                    "reason_codes": [history_error or "history_unknown"],
                    "duplicate": {"match_type": "unknown", "published": None},
                    "evidence_count": 0,
                    "verification": {"status": "pending_agent_06", "claims_for_verification": 0},
                    "persistence": {"candidate_state": "not_written", "evidence_state": "not_written"},
                })
                continue

            history_match = self._match_history(
                topic, str(candidate.get("draft_text") or "")[:20000], history
            )
            if history_match is not None:
                if history_match["published"] is True:
                    decision, reason = "BLOCK_DUPLICATE_PUBLISHED", history_match["match_type"]
                elif history_match["published"] is False:
                    decision, reason = "HOLD_PRIOR_GENERATION_REVIEW", "topic_or_content_seen_in_prior_ucos_run"
                else:
                    decision, reason = "HOLD_HISTORY_MATCH_STATUS_UNKNOWN", "matched_history_record_has_unknown_publish_status"
                results.append({
                    "topic": topic,
                    "platform": self.platform,
                    "niche": self.niche,
                    "decision": decision,
                    "reason_codes": [reason],
                    "duplicate": history_match,
                    "evidence_count": 0,
                    "verification": {"status": "pending_agent_06", "claims_for_verification": 0},
                    "persistence": {"candidate_state": "not_written", "evidence_state": "not_written"},
                })
                continue

            raw_evidence = candidate.get("evidence") or []
            evidence = self._normalize_evidence(raw_evidence)
            if len(evidence) < MIN_INDEPENDENT_SOURCES and self._evidence_provider is not None:
                try:
                    fetched = self._evidence_provider(topic, self.niche, MAX_EVIDENCE_PER_CANDIDATE)
                    evidence = self._normalize_evidence(list(raw_evidence or []) + list(fetched or []))
                except Exception:
                    warnings.append("evidence_provider_failed")

            independent_count = len({self._source_key(item["source"], item["url"]) for item in evidence})
            topic_digest = hashlib.sha256(
                f"{self.account_id}|{self.niche.casefold()}|{normalized_topic}".encode("utf-8")
            ).hexdigest()[:32]
            persistence = {"candidate_state": "not_written", "evidence_state": "not_written"}
            candidate_state_error = False
            if independent_count >= MIN_INDEPENDENT_SOURCES and self._has_durable_storage():
                try:
                    self._persist_candidate(run_id, topic_digest, topic, candidate, evidence)
                    persistence = {"candidate_state": "saved", "evidence_state": "saved"}
                except Exception:
                    candidate_state_error = True
                    warnings.append("research_state_persistence_failed")

            reason_codes: list[str] = []
            if not self._has_durable_storage():
                decision = "HOLD_RESEARCH_STORAGE_UNAVAILABLE"
                reason_codes.append("account_scoped_storage_not_configured")
            elif independent_count < MIN_INDEPENDENT_SOURCES:
                decision = "NEEDS_MORE_EVIDENCE"
                reason_codes.append("fewer_than_two_independent_sources")
            elif candidate_state_error:
                decision = "HOLD_RESEARCH_STATE_PERSISTENCE_FAILED"
                reason_codes.append("research_evidence_pack_not_persisted")
            else:
                decision = "READY_FOR_VERIFICATION"
                reason_codes.append("history_clear_and_source_attributed_evidence_pack_ready_for_agent_06")

            relevance = candidate.get("source_relevance_score")
            try:
                relevance = float(relevance)
                if not math.isfinite(relevance):
                    relevance = None
                elif relevance < 0 or relevance > 1:
                    # Tavily's relevance is in [0,1]; other providers can omit it.
                    relevance = None
            except (TypeError, ValueError):
                relevance = None

            claims = candidate.get("claims") or []
            if isinstance(claims, str):
                claims = [claims]
            if not isinstance(claims, Sequence) or isinstance(claims, (str, bytes)):
                claims = []
            claims = [
                str(item.get("claim") or item.get("text") or "").strip()[:2000]
                if isinstance(item, Mapping) else str(item or "").strip()[:2000]
                for item in list(claims)[:25]
            ]
            claims = [claim for claim in claims if claim]

            results.append({
                "topic": topic,
                "platform": self.platform,
                "niche": self.niche,
                "decision": decision,
                "reason_codes": reason_codes,
                "duplicate": {"match_type": "no_match", "published": False},
                "evidence": [
                    {
                        "source": item["source"],
                        "title": item["title"],
                        "url": item["url"],
                        "excerpt": item["content"][:1600],
                        "published_at": item["published_at"],
                    }
                    for item in evidence
                ],
                "evidence_count": len(evidence),
                "independent_source_count": independent_count,
                "source_relevance": {
                    "value": relevance,
                    "metric": "vendor_search_relevance_not_content_performance",
                },
                "claims_for_agent_06": claims,
                "verification": {
                    "status": "pending_agent_06",
                    "claims_for_verification": len(claims),
                },
                "next_agent": "AG06",
                "persistence": persistence,
            })

        report: dict[str, Any] = {
            "agent": self.name,
            "agent_id": self.agent_id,
            "agent_version": self.version,
            "run_id": run_id,
            "account_id": self.account_id,
            "platform": self.platform,
            "niche": self.niche,
            "started_at": started,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "status": (
                "completed" if results else
                "blocked_research_sources_unconfigured"
                if candidates is None and self._source_status.get("status") == "unconfigured"
                else "blocked_research_sources_unavailable"
                if candidates is None and self._source_status.get("status") == "unavailable"
                else "no_candidates"
            ),
            "research_sources": dict(self._source_status),
            "history": history_summary,
            "history_coverage": _HISTORY_COVERAGE,
            "candidate_count": len(results),
            "requested_candidate_limit": requested_limit,
            "effective_candidate_limit": limit,
            "candidate_limit_note": (
                "Tavily runs are capped at five candidate topics to bound external API use."
                if self._source is not None and requested_limit != limit else None
            ),
            "candidates": results,
            "recommended_topic": next(
                (item["topic"] for item in results if item.get("decision") == "READY_FOR_VERIFICATION"),
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
                if item.get("decision") == "READY_FOR_VERIFICATION":
                    item["decision"] = "HOLD_PERSISTENCE_UNAVAILABLE"
                    item["reason_codes"] = list(item["reason_codes"]) + ["research_report_not_persisted"]
            report["recommended_topic"] = None
            report["status"] = "blocked_persistence"
        if report["status"] == "completed" and not report["recommended_topic"]:
            report["status"] = "completed_with_holds"
        return report
