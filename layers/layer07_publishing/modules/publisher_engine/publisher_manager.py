"""L07 PublicationGateway orchestration.

Production publication uses the frozen v1.2 PostgreSQL publication ledger:
reserve -> PublishAttempt -> provider mutation -> provider effect -> verification.
Legacy SQLite repetition state is retained only for non-production migration/test
compatibility and is never consulted by the production path.
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from layers.layer07_publishing.modules.platform_plugin_manager.plugin_manager import PluginManager
from layers.layer07_publishing.modules.publisher_engine.publish_request import PublishRequest
from layers.layer07_publishing.modules.publisher_engine.publish_executor import PublishExecutor
from layers.layer07_publishing.modules.publisher_engine.upload_coordinator import UploadCoordinator, UploadResult
from layers.layer07_publishing.modules.publisher_engine.response_parser import ResponseParser
from layers.layer07_publishing.modules.publisher_engine.status_tracker import StatusTracker
from layers.layer07_publishing.modules.publisher_engine.publish_audit import PublishAudit
from layers.layer07_publishing.modules.publisher_engine.publish_result import PublisherResult
from layers.layer07_publishing.modules.publisher_engine.publisher_metrics import PublisherMetrics
from layers.layer07_publishing.modules.publisher_engine.content_repetition_guard import ContentRepetitionGuard
from layers.layer07_publishing.modules.publisher_engine.publication_ledger import (
    PublicationConflictError,
    PublicationLedger,
    UnresolvedPublicationError,
)


def _production_mode() -> bool:
    return os.environ.get("APP_ENV", "development").strip().lower() in {"production", "prod"}


class PublisherManager:
    """Shared L07 PublicationGateway for external publication semantics."""

    def __init__(
        self,
        plugin_manager: Optional[PluginManager] = None,
        executor: Optional[PublishExecutor] = None,
        uploader: Optional[UploadCoordinator] = None,
        parser: Optional[ResponseParser] = None,
        audit: Optional[PublishAudit] = None,
        metrics: Optional[PublisherMetrics] = None,
        repetition_guard: Optional[ContentRepetitionGuard] = None,
        publication_ledger: Optional[PublicationLedger] = None,
    ) -> None:
        self.plugin_manager = plugin_manager or PluginManager()
        self.executor = executor or PublishExecutor()
        self.uploader = uploader or UploadCoordinator()
        self.parser = parser or ResponseParser()
        self.audit = audit or PublishAudit()
        self.metrics = metrics or PublisherMetrics()
        self.repetition_guard = repetition_guard
        self.publication_ledger = publication_ledger
        if self.repetition_guard is None and not _production_mode():
            self.repetition_guard = ContentRepetitionGuard()
        self._events: List[Dict[str, Any]] = []
        self._request_count = 0

    @staticmethod
    def _account_repetition_guard(account_id: str) -> ContentRepetitionGuard:
        """Legacy account-local SQLite guard for non-production migration/tests."""
        if _production_mode():
            raise RuntimeError("legacy SQLite repetition guard is forbidden in production")
        from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
        registry = AccountRegistry()
        workspace = registry.workspace_path(account_id)
        workspace.mkdir(parents=True, exist_ok=True)
        return ContentRepetitionGuard(str(workspace / "publishing_history.sqlite3"))

    def _canonical_publish(self, request: PublishRequest, result: PublisherResult, tracker: StatusTracker) -> PublisherResult:
        ledger = self.publication_ledger or PublicationLedger()
        reservation = ledger.reserve(request)

        if reservation.reused:
            intent = ledger.get_intent(reservation.intent_id) or {}
            state = str(intent.get("state") or reservation.state)
            result.metadata.update({
                "publication_intent_id": reservation.intent_id,
                "publication_state": state,
                "idempotent_reuse": True,
            })
            if state == "VERIFIED_PUBLIC":
                effect = ledger.get_provider_effect(reservation.intent_id) or {}
                external_id = str(effect.get("external_post_id") or "").strip()
                external_url = str(effect.get("external_url") or "").strip()
                if not external_id:
                    result.set_error("verified publication has no external post identity", "ledger")
                    return result
                result.set_success(external_id, external_url)
                tracker.update("verified", f"Verified existing publication: {external_id}")
                return result
            result.set_error(
                f"publication intent remains {state}; reconciliation required before reuse",
                "pending",
            )
            result.metadata["pending"] = True
            return result

        provider = self._get_publisher(request.platform)
        if provider is None:
            ledger.record_provider_result(
                ledger.begin_attempt(reservation, request.platform),
                type("_Failure", (), {
                    "success": False,
                    "post_id": "",
                    "url": "",
                    "error_message": f"No plugin registered for '{request.platform}'",
                    "metadata": {"outcome": "confirmed_failure"},
                })(),
            )
            result.set_error(f"No plugin registered for '{request.platform}'", "plugin")
            result.metadata.update({"publication_intent_id": reservation.intent_id, "publication_state": "FAILED_CONFIRMED"})
            return result

        tracker.update("publishing", f"Publishing to {request.platform}")
        attempt = ledger.begin_attempt(reservation, request.platform)
        pub_result = self.executor.execute_publish(provider, request)
        state = ledger.record_provider_result(attempt, pub_result)
        metadata = dict(pub_result.metadata or {})
        result.metadata.update({
            "publication_intent_id": reservation.intent_id,
            "publish_attempt_id": attempt.attempt_id,
            "publication_state": state,
            "provider": attempt.provider,
        })
        if metadata.get("tracking_id"):
            result.metadata["provider_tracking_id"] = str(metadata["tracking_id"])
        external_id = str(pub_result.post_id or "").strip()
        if external_id:
            result.metadata["external_post_id"] = external_id

        if state == "FAILED_CONFIRMED":
            result.set_error(pub_result.error_message or "provider rejected publication", "provider")
            tracker.update("failed", result.error_message[:100])
            return result

        if state == "OUTCOME_UNKNOWN":
            result.set_error(
                "provider outcome is unknown; publication is held for reconciliation",
                "pending",
            )
            result.metadata["pending"] = True
            tracker.update("pending", "Provider outcome unknown; reconciliation required")
            return result

        if state != "SUBMITTED":
            result.set_error(f"unsupported publication state after provider call: {state}", "ledger")
            return result

        verification_state, evidence = self._verify_submission(
            provider, request, external_id, metadata
        )
        result.metadata["verification_evidence"] = evidence
        try:
            state = ledger.record_verification(
                reservation.intent_id,
                state=verification_state,
                evidence=evidence,
                next_reconcile_at=(
                    datetime.now(timezone.utc) + timedelta(seconds=30)
                    if verification_state in {
                        "VERIFYING", "VERIFICATION_UNKNOWN", "PUBLISHED_NOT_PUBLIC",
                        "RECONCILING", "IDENTITY_MISMATCH", "VERIFICATION_FAILED",
                    } else None
                ),
                expires_at=(
                    datetime.now(timezone.utc) + timedelta(hours=2)
                    if verification_state != "VERIFIED_PUBLIC" else None
                ),
            )
        except ValueError:
            raise

        result.metadata["publication_state"] = state
        if state == "VERIFIED_PUBLIC":
            result.set_success(external_id, str(evidence.get("canonical_url") or pub_result.url or ""))
            result.metadata["verified_public"] = True
            tracker.update("verified", f"Verified public publication: {external_id}")
            return result

        result.set_error(
            f"publication accepted but verification state is {state}; reconciliation required",
            "pending",
        )
        result.metadata["pending"] = True
        result.metadata["verified_public"] = False
        tracker.update("pending", f"Publication held in {state}")
        return result

    @staticmethod
    def _verify_submission(
        publisher: Any,
        request: PublishRequest,
        external_id: str,
        metadata: Dict[str, Any],
    ) -> tuple[str, Dict[str, Any]]:
        if not external_id:
            if metadata.get("tracking_id"):
                tracking_id = str(metadata["tracking_id"])
                status = ""
                try:
                    status = str(publisher.get_status(tracking_id) or "UNKNOWN")
                except Exception:
                    status = "UNKNOWN"
                return "VERIFICATION_UNKNOWN", {
                    "provider_tracking_id": tracking_id,
                    "provider_status": status,
                    "reason": "provider exposes a tracking identifier but no public object id",
                }
            return "VERIFICATION_UNKNOWN", {"reason": "provider returned no external post id"}

        try:
            post = publisher.get_post(external_id)
        except Exception as exc:
            return "VERIFICATION_UNKNOWN", {
                "external_post_id": external_id,
                "reason": f"provider lookup failed: {type(exc).__name__}",
            }
        if not isinstance(post, dict) or not post:
            return "VERIFICATION_UNKNOWN", {
                "external_post_id": external_id,
                "reason": "provider object not found during verification",
            }

        platform = request.platform
        platform_account_id = str(request.metadata.get("platform_account_id") or "").strip()
        evidence: Dict[str, Any] = {
            "external_post_id": external_id,
            "provider_object_present": True,
        }
        if platform == "facebook":
            owner = str(((post.get("from") or {}).get("id")) or "")
            is_published = post.get("is_published")
            is_hidden = post.get("is_hidden")
            canonical_url = str(post.get("permalink_url") or "")
            evidence.update({
                "owner_id": owner,
                "is_published": is_published,
                "is_hidden": is_hidden,
                "canonical_url": canonical_url,
            })
            if (
                is_published is True
                and is_hidden is not True
                and platform_account_id
                and owner == platform_account_id
                and canonical_url
            ):
                return "VERIFIED_PUBLIC", evidence
            if is_published is True and is_hidden is not True and canonical_url:
                return "IDENTITY_MISMATCH" if platform_account_id and owner != platform_account_id else "PUBLISHED_NOT_PUBLIC", evidence
            return "VERIFICATION_UNKNOWN", evidence

        if platform == "instagram":
            canonical_url = str(post.get("permalink") or post.get("permalink_url") or "")
            account_ok = False
            try:
                info = publisher.get_account_info()
                account_ok = bool(platform_account_id and str(info.get("id") or "") == platform_account_id)
                evidence["account_evidence"] = {"id": info.get("id"), "username": info.get("username")}
            except Exception:
                account_ok = False
            evidence["canonical_url"] = canonical_url
            if account_ok and post.get("id") and canonical_url:
                return "VERIFIED_PUBLIC", evidence
            return "VERIFICATION_UNKNOWN", evidence

        if platform == "pinterest":
            canonical_url = str(
                post.get("url")
                or post.get("permalink")
                or f"https://www.pinterest.com/pin/{external_id}/"
            )
            evidence["canonical_url"] = canonical_url
            evidence["pin_id"] = str(post.get("id") or external_id)
            if evidence["pin_id"] == external_id and canonical_url:
                return "VERIFIED_PUBLIC", evidence
            return "VERIFICATION_UNKNOWN", evidence

        canonical_url = str(post.get("url") or metadata.get("url") or "")
        evidence["canonical_url"] = canonical_url
        if canonical_url:
            return "VERIFIED_PUBLIC", evidence
        return "VERIFICATION_UNKNOWN", evidence

    def publish(self, request: PublishRequest) -> PublisherResult:
        result = PublisherResult(platform=request.platform)
        tracker = StatusTracker(request.request_id)
        start = time.time()

        errors = request.validate()
        if errors:
            result.set_error("; ".join(errors), "validation")
            tracker.update("failed", "Validation failed")
            self._record_event("publish_failed", request, result)
            return result

        try:
            if _production_mode():
                result = self._canonical_publish(request, result, tracker)
            else:
                result = self._legacy_publish(request, result, tracker)

            duration_ms = (time.time() - start) * 1000
            result.duration_ms = duration_ms
            self.audit.log(
                action="publish",
                platform=request.platform,
                request_id=request.request_id,
                post_id=result.post_id,
                success=result.success,
                duration_ms=duration_ms,
            )
            self.metrics.record_publish(result.success, duration_ms)
            self._request_count += 1
            self._record_event(
                "publish_completed" if result.success else "publish_failed",
                request,
                result,
            )
            return result
        except (PublicationConflictError, UnresolvedPublicationError, RuntimeError, ValueError) as exc:
            result.set_error(str(exc), "ledger")
            result.metadata.setdefault("publication_blocked", True)
            duration_ms = (time.time() - start) * 1000
            result.duration_ms = duration_ms
            self.audit.log(
                action="publish",
                platform=request.platform,
                request_id=request.request_id,
                post_id="",
                success=False,
                duration_ms=duration_ms,
            )
            self.metrics.record_publish(False, duration_ms)
            self._request_count += 1
            self._record_event("publish_failed", request, result)
            return result

    def _legacy_publish(self, request: PublishRequest, result: PublisherResult, tracker: StatusTracker) -> PublisherResult:
        reservation_id: Optional[int] = None
        guard = self.repetition_guard
        if guard is None:
            raise RuntimeError("legacy repetition guard unavailable outside production")
        account_id = request.metadata.get("account_id")
        if account_id and not request.metadata.get("repetition_reserved_by_pipeline"):
            guard = self._account_repetition_guard(str(account_id))
            decision = guard.reserve(
                account_id=str(account_id),
                platform=request.platform,
                content=request.content,
                template_id=(str(request.metadata["template_id"]) if request.metadata.get("template_id") else None),
            )
            if not decision.allowed:
                result.set_error(f"Content rejected by repetition gate: {decision.reason}", "repetition")
                tracker.update("failed", "Repetition gate rejected content")
                return result
            reservation_id = decision.reservation_id

        try:
            if request.has_media():
                tracker.update("uploading", f"Uploading {len(request.media_assets)} assets")
                upload_results = self.uploader.upload_assets(
                    request.media_assets, self._default_uploader
                )
                failed_uploads = [u for u in upload_results if not u.success]
                if failed_uploads:
                    result.set_error(f"Upload failed: {failed_uploads[0].error}", "upload")
                    tracker.update("failed", "Upload failed")
                    return result

            publisher = self._get_publisher(request.platform)
            if publisher is None:
                result.set_error(f"No plugin registered for '{request.platform}'", "plugin")
                return result

            pub_result = self.executor.execute_publish(publisher, request)
            if pub_result.success:
                result.set_success(pub_result.post_id, pub_result.url)
                if pub_result.metadata:
                    result.media_ids = pub_result.metadata.get("media_ids", [])
                tracker.update("published", f"Published: {pub_result.post_id}")
                if reservation_id is not None:
                    guard.finalize(reservation_id, pub_result.post_id)
                    reservation_id = None
            else:
                result.set_error(
                    pub_result.error_message,
                    self.parser.classify_error(pub_result.error_message),
                )
                tracker.update("failed", pub_result.error_message[:100])
            return result
        finally:
            if reservation_id is not None:
                guard.release(reservation_id)

    def publish_batch(self, requests: List[PublishRequest]) -> List[PublisherResult]:
        return [self.publish(req) for req in requests]

    def edit(self, platform: str, post_id: str, content: str) -> PublisherResult:
        result = PublisherResult(platform=platform)
        pub_result = self.executor.execute_edit(self._get_publisher(platform), post_id, content)
        if pub_result.success:
            result.set_success(pub_result.post_id, pub_result.url)
        else:
            result.set_error(pub_result.error_message, self.parser.classify_error(pub_result.error_message))
        self.audit.log(action="edit", platform=platform, post_id=post_id, success=result.success)
        return result

    def delete(self, platform: str, post_id: str) -> bool:
        success = self.executor.execute_delete(self._get_publisher(platform), post_id)
        self.audit.log(action="delete", platform=platform, post_id=post_id, success=success)
        return success

    def get_status(self, platform: str, post_id: str) -> str:
        return self.plugin_manager.get_status(platform, post_id)

    def _get_publisher(self, platform: str):
        return self.plugin_manager.registry.get_instance(platform)

    def _default_uploader(self, asset: Any) -> UploadResult:
        result = UploadResult(asset.asset_id or asset.file_name)
        result.success = True
        result.media_id = f"media_{asset.file_name}"
        return result

    def _record_event(self, event: str, request: PublishRequest, result: PublisherResult) -> None:
        self._events.append({
            "event": event,
            "request_id": request.request_id,
            "platform": request.platform,
            "success": result.success,
            "post_id": result.post_id,
            "timestamp": time.time(),
        })

    @property
    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)

    @property
    def request_count(self) -> int:
        return self._request_count
