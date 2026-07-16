"""Publisher Manager — Orchestrate the full publishing pipeline."""
from __future__ import annotations
import itertools
import time
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

_MANAGER_COUNTER = itertools.count(1)


class PublisherManager:
    """Orchestrate the full publishing pipeline.

    Flow: Request → Validate → Upload → Publish → Parse → Result → Audit
    """

    def __init__(
        self,
        plugin_manager: Optional[PluginManager] = None,
        executor: Optional[PublishExecutor] = None,
        uploader: Optional[UploadCoordinator] = None,
        parser: Optional[ResponseParser] = None,
        audit: Optional[PublishAudit] = None,
        metrics: Optional[PublisherMetrics] = None,
    ) -> None:
        self.plugin_manager = plugin_manager or PluginManager()
        self.executor = executor or PublishExecutor()
        self.uploader = uploader or UploadCoordinator()
        self.parser = parser or ResponseParser()
        self.audit = audit or PublishAudit()
        self.metrics = metrics or PublisherMetrics()
        self._events: List[Dict[str, Any]] = []
        self._request_count = 0

    def publish(self, request: PublishRequest) -> PublisherResult:
        """Execute full publish pipeline for a single request."""
        result = PublisherResult(platform=request.platform)
        tracker = StatusTracker(request.request_id)
        start = time.time()

        # Step 1: Validate
        errors = request.validate()
        if errors:
            result.set_error("; ".join(errors), "validation")
            tracker.update("failed", "Validation failed")
            self._record_event("publish_failed", request, result)
            return result

        # Step 2: Upload media (if any)
        if request.has_media():
            tracker.update("uploading", f"Uploading {len(request.media_assets)} assets")
            upload_results = self.uploader.upload_assets(
                request.media_assets, self._default_uploader
            )
            failed_uploads = [u for u in upload_results if not u.success]
            if failed_uploads:
                first_err = failed_uploads[0].error
                result.set_error(f"Upload failed: {first_err}", "upload")
                tracker.update("failed", "Upload failed")
                self._record_event("publish_failed", request, result)
                return result

        # Step 3: Execute publish
        tracker.update("publishing", f"Publishing to {request.platform}")
        pub_result = self.executor.execute_publish(
            self._get_publisher(request.platform), request
        )

        # Step 4: Parse response
        if pub_result.success:
            result.set_success(pub_result.post_id, pub_result.url)
            if pub_result.metadata:
                result.media_ids = pub_result.metadata.get("media_ids", [])
            tracker.update("published", f"Published: {pub_result.post_id}")
        else:
            error_cat = self.parser.classify_error(pub_result.error_message)
            result.set_error(pub_result.error_message, error_cat)
            tracker.update("failed", pub_result.error_message[:100])

        # Step 5: Audit
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
        self._record_event("publish_completed" if result.success else "publish_failed", request, result)
        return result

    def publish_batch(
        self,
        requests: List[PublishRequest],
    ) -> List[PublisherResult]:
        return [self.publish(req) for req in requests]

    def edit(
        self,
        platform: str,
        post_id: str,
        content: str,
    ) -> PublisherResult:
        result = PublisherResult(platform=platform)
        pub_result = self.executor.execute_edit(
            self._get_publisher(platform), post_id, content
        )
        if pub_result.success:
            result.set_success(pub_result.post_id, pub_result.url)
        else:
            cat = self.parser.classify_error(pub_result.error_message)
            result.set_error(pub_result.error_message, cat)
        self.audit.log(
            action="edit", platform=platform, post_id=post_id,
            success=result.success,
        )
        return result

    def delete(self, platform: str, post_id: str) -> bool:
        success = self.executor.execute_delete(
            self._get_publisher(platform), post_id
        )
        self.audit.log(
            action="delete", platform=platform, post_id=post_id,
            success=success,
        )
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
