"""Publisher Manager — Orchestrate the full publishing pipeline."""
from __future__ import annotations
import itertools
import time
from pathlib import Path
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

_MANAGER_COUNTER = itertools.count(1)


class PublisherManager:
    """Orchestrate validate → account-local repetition gate → upload → publish → audit."""

    def __init__(self, plugin_manager: Optional[PluginManager] = None,
                 executor: Optional[PublishExecutor] = None,
                 uploader: Optional[UploadCoordinator] = None,
                 parser: Optional[ResponseParser] = None,
                 audit: Optional[PublishAudit] = None,
                 metrics: Optional[PublisherMetrics] = None,
                 repetition_guard: Optional[ContentRepetitionGuard] = None) -> None:
        self.plugin_manager = plugin_manager or PluginManager()
        self.executor = executor or PublishExecutor()
        self.uploader = uploader or UploadCoordinator()
        self.parser = parser or ResponseParser()
        self.audit = audit or PublishAudit()
        self.metrics = metrics or PublisherMetrics()
        self.repetition_guard = repetition_guard or ContentRepetitionGuard()
        self._events: List[Dict[str, Any]] = []
        self._request_count = 0

    @staticmethod
    def _account_repetition_guard(account_id: str) -> ContentRepetitionGuard:
        """Return a physically separate repetition database for this account."""
        from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
        registry = AccountRegistry()
        workspace = registry.workspace_path(account_id)
        workspace.mkdir(parents=True, exist_ok=True)
        return ContentRepetitionGuard(str(workspace / "publishing_history.sqlite3"))

    def publish(self, request: PublishRequest) -> PublisherResult:
        result = PublisherResult(platform=request.platform)
        tracker = StatusTracker(request.request_id)
        start = time.time()
        reservation_id: Optional[int] = None
        guard = self.repetition_guard

        errors = request.validate()
        if errors:
            result.set_error("; ".join(errors), "validation")
            tracker.update("failed", "Validation failed")
            self._record_event("publish_failed", request, result)
            return result

        account_id = request.metadata.get("account_id")
        if account_id:
            guard = self._account_repetition_guard(str(account_id))
            decision = guard.reserve(
                account_id=str(account_id), platform=request.platform,
                content=request.content,
                template_id=(str(request.metadata["template_id"])
                             if request.metadata.get("template_id") else None),
            )
            if not decision.allowed:
                result.set_error(f"Content rejected by repetition gate: {decision.reason}", "repetition")
                tracker.update("failed", "Repetition gate rejected content")
                self._record_event("publish_rejected_repetition", request, result)
                return result
            reservation_id = decision.reservation_id

        try:
            if request.has_media():
                tracker.update("uploading", f"Uploading {len(request.media_assets)} assets")
                upload_results = self.uploader.upload_assets(request.media_assets, self._default_uploader)
                failed_uploads = [u for u in upload_results if not u.success]
                if failed_uploads:
                    result.set_error(f"Upload failed: {failed_uploads[0].error}", "upload")
                    tracker.update("failed", "Upload failed")
                    self._record_event("publish_failed", request, result)
                    return result

            tracker.update("publishing", f"Publishing to {request.platform}")
            publisher = self._get_publisher(request.platform)
            if publisher is None:
                result.set_error(f"No plugin registered for '{request.platform}'", "plugin")
            else:
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
                    result.set_error(pub_result.error_message, self.parser.classify_error(pub_result.error_message))
                    tracker.update("failed", pub_result.error_message[:100])

            duration_ms = (time.time() - start) * 1000
            result.duration_ms = duration_ms
            self.audit.log(action="publish", platform=request.platform, request_id=request.request_id,
                           post_id=result.post_id, success=result.success, duration_ms=duration_ms)
            self.metrics.record_publish(result.success, duration_ms)
            self._request_count += 1
            self._record_event("publish_completed" if result.success else "publish_failed", request, result)
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
        self._events.append({"event": event, "request_id": request.request_id,
                             "platform": request.platform, "success": result.success,
                             "post_id": result.post_id, "timestamp": time.time()})

    @property
    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)

    @property
    def request_count(self) -> int:
        return self._request_count
