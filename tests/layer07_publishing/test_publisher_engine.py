"""Tests for Layer 7 Module 5 — Publisher Engine."""
import time
from layers.layer07_publishing.modules.publisher_engine.publish_request import PublishRequest
from layers.layer07_publishing.modules.publisher_engine.publish_executor import PublishExecutor
from layers.layer07_publishing.modules.publisher_engine.upload_coordinator import (
    UploadCoordinator, UploadResult,
)
from layers.layer07_publishing.modules.publisher_engine.response_parser import ResponseParser
from layers.layer07_publishing.modules.publisher_engine.status_tracker import (
    StatusTracker, PUBLISH_STATUSES,
)
from layers.layer07_publishing.modules.publisher_engine.publish_transaction import (
    PublishTransaction,
)
from layers.layer07_publishing.modules.publisher_engine.publish_audit import PublishAudit
from layers.layer07_publishing.modules.publisher_engine.publish_result import PublisherResult
from layers.layer07_publishing.modules.publisher_engine.publisher_metrics import PublisherMetrics
from layers.layer07_publishing.modules.publisher_engine.publisher_manager import PublisherManager
from layers.layer07_publishing.modules.publisher_engine.exceptions import (
    PublishError, PublishValidationError, PublishExecutionError, UploadError, RollbackError,
)
from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import (
    BasePublisher, PublishResult, PlatformCapabilities,
)
from layers.layer07_publishing.modules.platform_plugin_manager.plugin_manager import PluginManager
from layers.layer07_publishing.modules.media_manager.media_asset import MediaAsset


# ─── Mock Publisher ──────────────────────────────────────────────────
class MockPublisher(BasePublisher):
    def __init__(self) -> None:
        self.published = False
        self.deleted = False
        self._fail = False

    def get_platform_name(self) -> str:
        return "mock"

    def get_capabilities(self) -> PlatformCapabilities:
        caps = PlatformCapabilities()
        caps.supports_images = True
        caps.supports_edit = True
        caps.supports_delete = True
        return caps

    def authenticate(self, credentials):
        return True

    def validate(self, content, content_type="post"):
        return bool(content)

    def publish(self, content, media_paths=None, content_type="post", **kwargs):
        if self._fail:
            return PublishResult(success=False, platform="mock")
        self.published = True
        result = PublishResult(success=True, platform="mock")
        result.post_id = "mock_post_1"
        result.url = "https://mock.test/post/1"
        return result

    def edit(self, post_id, content, **kwargs):
        result = PublishResult(success=True, platform="mock")
        result.post_id = post_id
        return result

    def delete(self, post_id):
        self.deleted = True
        return True

    def get_post(self, post_id):
        return {"id": post_id, "content": "test"}

    def get_status(self, post_id):
        return "published"

    def get_analytics(self, post_id):
        return {"likes": 10}

    def schedule(self, content, scheduled_time, media_paths=None, **kwargs):
        result = PublishResult(success=True, platform="mock")
        result.post_id = "mock_scheduled_1"
        return result


# ─── PublishRequest Tests ────────────────────────────────────────────
class TestPublishRequest:
    def test_create_default(self):
        req = PublishRequest()
        assert req.request_id.startswith("req_")
        assert req.platform == ""
        assert req.content == ""
        assert req.content_type == "post"

    def test_create_with_args(self):
        req = PublishRequest(platform="facebook", content="Hello", content_type="post")
        assert req.platform == "facebook"
        assert req.content == "Hello"
        assert req.content_type == "post"

    def test_has_media_false(self):
        req = PublishRequest()
        assert req.has_media() is False

    def test_has_media_true(self):
        req = PublishRequest()
        req.media_assets = [MediaAsset("/img.png")]
        assert req.has_media() is True

    def test_get_media_paths(self):
        req = PublishRequest()
        req.media_assets = [MediaAsset("/img.png"), MediaAsset("/vid.mp4")]
        paths = req.get_media_paths()
        assert "/img.png" in paths
        assert "/vid.mp4" in paths

    def test_validate_missing_platform(self):
        req = PublishRequest(content="Hello")
        errors = req.validate()
        assert any("Platform" in e for e in errors)

    def test_validate_missing_content_and_media(self):
        req = PublishRequest(platform="facebook")
        errors = req.validate()
        assert any("Content or media" in e for e in errors)

    def test_validate_content_too_long(self):
        req = PublishRequest(platform="facebook", content="x" * 50001)
        errors = req.validate()
        assert any("50000" in e for e in errors)

    def test_validate_valid(self):
        req = PublishRequest(platform="facebook", content="Hello")
        assert req.is_valid() is True
        assert req.validate() == []

    def test_validate_scheduled_past(self):
        req = PublishRequest(platform="facebook", content="Hi")
        req.scheduled = True
        req.scheduled_time = time.time() - 100
        errors = req.validate()
        assert any("future" in e for e in errors)

    def test_to_dict(self):
        req = PublishRequest(platform="fb", content="Hi")
        d = req.to_dict()
        assert d["platform"] == "fb"
        assert d["content_length"] == 2
        assert "request_id" in d


# ─── PublishExecutor Tests ───────────────────────────────────────────
class TestPublishExecutor:
    def setup_method(self):
        self.executor = PublishExecutor()
        self.pub = MockPublisher()

    def test_execute_publish_success(self):
        req = PublishRequest(platform="mock", content="Hello")
        result = self.executor.execute_publish(self.pub, req)
        assert result.success is True
        assert result.post_id == "mock_post_1"
        assert self.executor.execution_count == 1

    def test_execute_publish_exception(self):
        class FailPublisher(MockPublisher):
            def publish(self, content, media_paths=None, **kwargs):
                raise RuntimeError("API down")
        req = PublishRequest(platform="mock", content="Hi")
        result = self.executor.execute_publish(FailPublisher(), req)
        assert result.success is False
        assert "API down" in result.error_message

    def test_execute_edit(self):
        result = self.executor.execute_edit(self.pub, "p1", "New content")
        assert result.success is True
        assert result.post_id == "p1"

    def test_execute_edit_exception(self):
        class FailPub(MockPublisher):
            def edit(self, post_id, content, **kwargs):
                raise RuntimeError("Edit failed")
        result = self.executor.execute_edit(FailPub(), "p1", "content")
        assert result.success is False

    def test_execute_delete(self):
        assert self.executor.execute_delete(self.pub, "p1") is True
        assert self.pub.deleted is True

    def test_execute_delete_exception(self):
        class FailPub(MockPublisher):
            def delete(self, post_id):
                raise RuntimeError("Delete failed")
        assert self.executor.execute_delete(FailPub(), "p1") is False

    def test_execute_reschedule(self):
        req = PublishRequest(platform="mock", content="Hi")
        future = time.time() + 3600
        result = self.executor.execute_reschedule(self.pub, req, future)
        assert result.success is True
        assert req.scheduled is True
        assert req.scheduled_time == future

    def test_avg_time_ms(self):
        req = PublishRequest(platform="mock", content="Hi")
        self.executor.execute_publish(self.pub, req)
        assert self.executor.avg_time_ms >= 0


# ─── UploadCoordinator Tests ─────────────────────────────────────────
class TestUploadCoordinator:
    def setup_method(self):
        self.uc = UploadCoordinator()

    def test_upload_assets_success(self):
        def success_uploader(a):
            r = UploadResult(a.file_name)
            r.success = True
            return r
        assets = [MediaAsset("/img.png"), MediaAsset("/vid.mp4")]
        results = self.uc.upload_assets(assets, success_uploader)
        assert len(results) == 2
        assert all(r.success for r in results)

    def test_upload_assets_failure(self):
        def fail_uploader(a):
            r = UploadResult(a.file_name)
            r.error = "Upload failed"
            return r
        assets = [MediaAsset("/bad.png")]
        results = self.uc.upload_assets(assets, fail_uploader)
        assert results[0].success is False

    def test_upload_assets_exception(self):
        def boom(a):
            raise RuntimeError("Network error")
        results = self.uc.upload_assets([MediaAsset("/x.png")], boom)
        assert len(results) == 1
        assert "Network error" in results[0].error

    def test_validate_assets_ok(self):
        assets = [MediaAsset("/a.png"), MediaAsset("/b.png")]
        errors = self.uc.validate_assets(assets)
        assert errors == []

    def test_validate_assets_too_many(self):
        assets = [MediaAsset(f"/a{i}.png") for i in range(15)]
        errors = self.uc.validate_assets(assets, max_count=10)
        assert len(errors) == 1
        assert "Too many" in errors[0]

    def test_validate_assets_no_path(self):
        assets = [MediaAsset("")]
        errors = self.uc.validate_assets(assets)
        assert any("no file path" in e for e in errors)

    def test_get_upload_summary(self):
        r1 = UploadResult("a")
        r1.success = True
        r2 = UploadResult("b")
        r2.success = False
        summary = self.uc.get_upload_summary([r1, r2])
        assert summary["successful"] == 1
        assert summary["failed"] == 1

    def test_upload_count(self):
        def success_uploader(a):
            r = UploadResult(a.file_name)
            r.success = True
            return r
        assets = [MediaAsset("/a.png"), MediaAsset("/b.png")]
        self.uc.upload_assets(assets, success_uploader)
        assert self.uc.upload_count == 2

    def test_upload_result_to_dict(self):
        r = UploadResult("asset_1")
        r.success = True
        r.url = "https://cdn.test/img.png"
        d = r.to_dict()
        assert d["asset_id"] == "asset_1"
        assert d["success"] is True


# ─── ResponseParser Tests ────────────────────────────────────────────
class TestResponseParser:
    def setup_method(self):
        self.parser = ResponseParser()

    def test_parse_success(self):
        raw = {"id": "12345", "url": "https://fb.test/post/12345"}
        parsed = self.parser.parse_publish_response(raw, "facebook")
        assert parsed["success"] is True
        assert parsed["post_id"] == "12345"
        assert parsed["url"] == "https://fb.test/post/12345"

    def test_parse_with_error(self):
        raw = {"error": "Rate limited"}
        parsed = self.parser.parse_publish_response(raw, "facebook")
        assert parsed["success"] is False
        assert "Rate limited" in parsed["error"]

    def test_extract_post_id_nested(self):
        raw = {"data": {"id": "nested_123"}}
        assert self.parser.extract_post_id(raw) == "nested_123"

    def test_extract_post_id_missing(self):
        raw = {"foo": "bar"}
        assert self.parser.extract_post_id(raw) == ""

    def test_extract_url_nested(self):
        raw = {"data": {"url": "https://test.com/1"}}
        assert self.parser.extract_url(raw) == "https://test.com/1"

    def test_extract_media_ids(self):
        raw = {"media_ids": ["m1", "m2"]}
        ids = self.parser.extract_media_ids(raw)
        assert ids == ["m1", "m2"]

    def test_extract_error_dict(self):
        raw = {"error": {"message": "Invalid token"}}
        assert self.parser.extract_error(raw) == "Invalid token"

    def test_classify_rate_limit(self):
        assert self.parser.classify_error("Rate limit exceeded") == "rate_limit"

    def test_classify_auth_error(self):
        assert self.parser.classify_error("Unauthorized access") == "auth_error"

    def test_classify_not_found(self):
        assert self.parser.classify_error("Post not found") == "not_found"

    def test_classify_network_error(self):
        assert self.parser.classify_error("Connection timeout") == "network_error"

    def test_classify_unknown(self):
        assert self.parser.classify_error("Something weird") == "unknown"

    def test_is_retryable_rate_limit(self):
        assert self.parser.is_retryable("Rate limit exceeded") is True

    def test_is_retryable_auth_error(self):
        assert self.parser.is_retryable("Unauthorized") is False


# ─── StatusTracker Tests ─────────────────────────────────────────────
class TestStatusTracker:
    def setup_method(self):
        self.tracker = StatusTracker("req_1")

    def test_initial_status(self):
        assert self.tracker.current_status == "pending"

    def test_update_valid(self):
        self.tracker.update("uploading", "Starting upload")
        assert self.tracker.current_status == "uploading"

    def test_update_invalid(self):
        try:
            self.tracker.update("bogus")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_get_history(self):
        self.tracker.update("publishing")
        history = self.tracker.get_history()
        assert len(history) == 2
        assert history[0]["status"] == "pending"
        assert history[1]["status"] == "publishing"

    def test_is_terminal(self):
        self.tracker.update("published")
        assert self.tracker.is_terminal() is True

    def test_is_not_terminal(self):
        self.tracker.update("uploading")
        assert self.tracker.is_terminal() is False

    def test_is_success(self):
        self.tracker.update("published")
        assert self.tracker.is_success() is True

    def test_transition_count(self):
        self.tracker.update("uploading")
        self.tracker.update("publishing")
        assert self.tracker.transition_count() == 2

    def test_all_statuses_valid(self):
        for status in PUBLISH_STATUSES:
            t = StatusTracker()
            t.update(status)
            assert t.current_status == status

    def test_to_dict(self):
        d = self.tracker.to_dict()
        assert d["request_id"] == "req_1"
        assert "current_status" in d


# ─── PublishTransaction Tests ────────────────────────────────────────
class TestPublishTransaction:
    def setup_method(self):
        self.txn = PublishTransaction("txn_1")

    def test_create(self):
        assert self.txn.transaction_id == "txn_1"
        assert self.txn.is_completed is False
        assert self.txn.step_count == 0

    def test_add_step(self):
        self.txn.add_step("validate", lambda: True)
        assert self.txn.step_count == 1

    def test_execute(self):
        self.txn.add_step("step1", lambda: True)
        self.txn.add_step("step2", lambda: True)
        assert self.txn.execute() is True
        assert self.txn.is_completed is True

    def test_rollback(self):
        rolled_back = []
        self.txn.add_step("s1", lambda: True, lambda: (rolled_back.append("s1"), True)[1])
        self.txn.add_step("s2", lambda: True, lambda: (rolled_back.append("s2"), True)[1])
        self.txn.execute()
        assert self.txn.rollback() is True
        assert self.txn.is_rolled_back is True
        assert rolled_back == ["s2", "s1"]  # reversed order

    def test_get_steps(self):
        self.txn.add_step("step_a", lambda: True)
        steps = self.txn.get_steps()
        assert len(steps) == 1
        assert steps[0]["name"] == "step_a"

    def test_to_dict(self):
        self.txn.add_step("s", lambda: True)
        self.txn.execute()
        d = self.txn.to_dict()
        assert d["completed"] is True
        assert d["steps"] == 1

    def test_rollback_without_fns(self):
        self.txn.add_step("s1", lambda: True)
        self.txn.execute()
        assert self.txn.rollback() is True


# ─── PublishAudit Tests ──────────────────────────────────────────────
class TestPublishAudit:
    def setup_method(self):
        self.audit = PublishAudit()

    def test_log_entry(self):
        entry = self.audit.log("publish", "facebook", request_id="r1", success=True)
        assert entry.entry_id.startswith("audit_")
        assert entry.action == "publish"
        assert entry.success is True

    def test_get_entries_all(self):
        self.audit.log("publish", "facebook")
        self.audit.log("edit", "linkedin")
        assert self.audit.entry_count == 2

    def test_get_entries_by_platform(self):
        self.audit.log("publish", "facebook")
        self.audit.log("publish", "linkedin")
        entries = self.audit.get_entries(platform="facebook")
        assert len(entries) == 1

    def test_get_entries_by_action(self):
        self.audit.log("publish", "facebook")
        self.audit.log("edit", "facebook")
        entries = self.audit.get_entries(action="edit")
        assert len(entries) == 1

    def test_success_rate(self):
        self.audit.log("publish", success=True)
        self.audit.log("publish", success=True)
        self.audit.log("publish", success=False)
        assert self.audit.get_success_rate() > 0.6

    def test_success_rate_empty(self):
        assert self.audit.get_success_rate() == 0.0

    def test_get_stats(self):
        self.audit.log("publish", "fb", success=True, duration_ms=100)
        self.audit.log("publish", "fb", success=False, duration_ms=200)
        stats = self.audit.get_stats()
        assert stats["total"] == 2
        assert stats["successful"] == 1
        assert "fb" in stats["platforms"]

    def test_entry_to_dict(self):
        entry = self.audit.log("delete", "linkedin")
        d = entry.to_dict()
        assert d["action"] == "delete"
        assert d["platform"] == "linkedin"


# ─── PublisherResult Tests ───────────────────────────────────────────
class TestPublisherResult:
    def test_create_default(self):
        r = PublisherResult()
        assert r.result_id.startswith("res_")
        assert r.success is False

    def test_set_success(self):
        r = PublisherResult()
        r.set_success("post_123", "https://test.com/123")
        assert r.success is True
        assert r.post_id == "post_123"
        assert r.url == "https://test.com/123"

    def test_set_error(self):
        r = PublisherResult()
        r.set_error("Rate limited", "rate_limit")
        assert r.success is False
        assert r.error_category == "rate_limit"

    def test_to_dict(self):
        r = PublisherResult(success=True, platform="facebook")
        r.set_success("p1", "https://test.com")
        d = r.to_dict()
        assert d["platform"] == "facebook"
        assert d["post_id"] == "p1"
        assert d["success"] is True

    def test_error_truncation(self):
        r = PublisherResult()
        r.set_error("x" * 600)
        assert len(r.error_message) <= 500


# ─── PublisherMetrics Tests ──────────────────────────────────────────
class TestPublisherMetrics:
    def setup_method(self):
        self.metrics = PublisherMetrics()

    def test_record_publish_success(self):
        self.metrics.record_publish(True, 150.0)
        snap = self.metrics.get_current()
        assert snap["publish_count"] == 1
        assert snap["success_count"] == 1
        assert snap["failure_count"] == 0

    def test_record_publish_failure(self):
        self.metrics.record_publish(False, 50.0)
        snap = self.metrics.get_current()
        assert snap["failure_count"] == 1

    def test_record_upload(self):
        self.metrics.record_upload(1024)
        snap = self.metrics.get_current()
        assert snap["upload_count"] == 1
        assert snap["upload_bytes"] == 1024

    def test_record_api_call(self):
        self.metrics.record_api_call(25.5)
        snap = self.metrics.get_current()
        assert snap["api_call_count"] == 1
        assert snap["avg_api_latency_ms"] == 25.5

    def test_take_snapshot(self):
        self.metrics.record_publish(True, 100)
        snap = self.metrics.take_snapshot()
        assert len(self.metrics.get_snapshots()) == 1

    def test_reset(self):
        self.metrics.record_publish(True, 100)
        self.metrics.reset()
        snap = self.metrics.get_current()
        assert snap["publish_count"] == 0

    def test_success_rate(self):
        self.metrics.record_publish(True, 100)
        self.metrics.record_publish(True, 100)
        self.metrics.record_publish(False, 100)
        snap = self.metrics.get_current()
        assert snap["success_rate"] > 0.6


# ─── PublisherManager Tests ──────────────────────────────────────────
class TestPublisherManager:
    def setup_method(self):
        self.registry = PluginManager()
        self.registry.register("mock", MockPublisher)
        self.mgr = PublisherManager(plugin_manager=self.registry)

    def test_publish_success(self):
        req = PublishRequest(platform="mock", content="Hello World")
        result = self.mgr.publish(req)
        assert result.success is True
        assert result.post_id == "mock_post_1"

    def test_publish_validation_error(self):
        req = PublishRequest()  # empty = invalid
        result = self.mgr.publish(req)
        assert result.success is False
        assert result.error_category == "validation"

    def test_publish_with_media(self):
        req = PublishRequest(platform="mock", content="Post with image")
        asset = MediaAsset("/test.png")
        asset.file_path = "/test.png"
        req.media_assets = [asset]
        result = self.mgr.publish(req)
        assert result.success is True

    def test_publish_batch(self):
        reqs = [
            PublishRequest(platform="mock", content="Post 1"),
            PublishRequest(platform="mock", content="Post 2"),
        ]
        results = self.mgr.publish_batch(reqs)
        assert len(results) == 2
        assert all(r.success for r in results)

    def test_edit(self):
        result = self.mgr.edit("mock", "post_123", "Updated content")
        assert result.success is True

    def test_delete(self):
        assert self.mgr.delete("mock", "post_123") is True

    def test_get_status(self):
        status = self.mgr.get_status("mock", "post_1")
        assert status == "published"

    def test_events_tracked(self):
        req = PublishRequest(platform="mock", content="Hi")
        self.mgr.publish(req)
        events = self.mgr.events
        assert len(events) >= 1
        assert events[0]["event"] == "publish_completed"

    def test_request_count(self):
        self.mgr.publish(PublishRequest(platform="mock", content="1"))
        self.mgr.publish(PublishRequest(platform="mock", content="2"))
        assert self.mgr.request_count == 2

    def test_audit_populated(self):
        self.mgr.publish(PublishRequest(platform="mock", content="Hi"))
        assert self.mgr.audit.entry_count >= 1

    def test_metrics_populated(self):
        self.mgr.publish(PublishRequest(platform="mock", content="Hi"))
        snap = self.mgr.metrics.get_current()
        assert snap["publish_count"] >= 1

    def test_publish_unregistered_platform(self):
        req = PublishRequest(platform="nonexistent", content="Hi")
        result = self.mgr.publish(req)
        assert result.success is False


# ─── Exceptions Tests ────────────────────────────────────────────────
class TestExceptions:
    def test_publish_error_hierarchy(self):
        assert issubclass(PublishError, Exception)
        assert issubclass(PublishValidationError, PublishError)
        assert issubclass(PublishExecutionError, PublishError)
        assert issubclass(UploadError, PublishError)
        assert issubclass(RollbackError, PublishError)

    def test_publish_error_message(self):
        err = PublishError("test error")
        assert str(err) == "test error"

    def test_catch_publish_error(self):
        try:
            raise PublishExecutionError("exec failed")
        except PublishError:
            pass  # caught
