"""Tests for Layer 7 Module 2 — Platform Plugin Manager."""
from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import (
    PublishResult, PlatformCapabilities,
)
from layers.layer07_publishing.modules.platform_plugin_manager.plugin_registry import PluginRegistry
from layers.layer07_publishing.modules.platform_plugin_manager.mock_publisher import MockPublisher
from layers.layer07_publishing.modules.platform_plugin_manager.plugin_manager import PluginManager
from layers.layer07_publishing.modules.platform_plugin_manager.exceptions import PluginNotFoundError


# ── PublishResult Tests ──

class TestPublishResult:
    def test_success_result(self):
        r = PublishResult(success=True, platform="facebook")
        assert r.success
        assert r.platform == "facebook"

    def test_to_dict(self):
        r = PublishResult(success=True, platform="twitter")
        r.post_id = "tw_123"
        d = r.to_dict()
        assert d["post_id"] == "tw_123"
        assert d["success"] is True


# ── PlatformCapabilities Tests ──

class TestPlatformCapabilities:
    def test_default_caps(self):
        caps = PlatformCapabilities()
        assert not caps.supports_images
        assert caps.max_length == 10000

    def test_supports_method(self):
        caps = PlatformCapabilities()
        caps.supports_images = True
        assert caps.supports("images")
        assert not caps.supports("polls")

    def test_to_dict(self):
        caps = PlatformCapabilities()
        caps.supports_video = True
        d = caps.to_dict()
        assert d["supports_video"] is True


# ── PluginRegistry Tests ──

class TestPluginRegistry:
    def setup_method(self):
        self.registry = PluginRegistry()

    def test_register(self):
        self.registry.register("mock", MockPublisher)
        assert self.registry.is_registered("mock")

    def test_get_class(self):
        self.registry.register("mock", MockPublisher)
        cls = self.registry.get_class("mock")
        assert cls is MockPublisher

    def test_get_instance(self):
        self.registry.register("mock", MockPublisher)
        instance = self.registry.get_instance("mock")
        assert isinstance(instance, MockPublisher)

    def test_get_instance_singleton(self):
        self.registry.register("mock", MockPublisher)
        i1 = self.registry.get_instance("mock")
        i2 = self.registry.get_instance("mock")
        assert i1 is i2

    def test_unregister(self):
        self.registry.register("mock", MockPublisher)
        assert self.registry.unregister("mock")
        assert not self.registry.is_registered("mock")

    def test_list_platforms(self):
        self.registry.register("facebook", MockPublisher)
        self.registry.register("linkedin", MockPublisher)
        platforms = self.registry.list_platforms()
        assert "facebook" in platforms
        assert "linkedin" in platforms

    def test_list_capabilities(self):
        self.registry.register("mock", MockPublisher)
        caps = self.registry.list_capabilities()
        assert "mock" in caps

    def test_count(self):
        self.registry.register("a", MockPublisher)
        self.registry.register("b", MockPublisher)
        assert self.registry.count == 2


# ── MockPublisher Tests ──

class TestMockPublisher:
    def setup_method(self):
        self.pub = MockPublisher("test_platform")

    def test_get_platform_name(self):
        assert self.pub.get_platform_name() == "test_platform"

    def test_get_capabilities(self):
        caps = self.pub.get_capabilities()
        assert caps.supports_images
        assert caps.supports_video

    def test_authenticate(self):
        assert self.pub.authenticate({"token": "test"})
        assert self.pub._authenticated

    def test_validate(self):
        assert self.pub.validate("Hello world")
        assert not self.pub.validate("")

    def test_publish(self):
        result = self.pub.publish("Test content")
        assert result.success
        assert result.post_id != ""

    def test_edit(self):
        result = self.pub.publish("Original")
        edited = self.pub.edit(result.post_id, "Edited")
        assert edited.success

    def test_delete(self):
        result = self.pub.publish("To delete")
        assert self.pub.delete(result.post_id)
        assert self.pub.get_post(result.post_id) is None

    def test_get_post(self):
        result = self.pub.publish("Content")
        post = self.pub.get_post(result.post_id)
        assert post is not None

    def test_get_status(self):
        result = self.pub.publish("Content")
        assert self.pub.get_status(result.post_id) == "published"
        assert self.pub.get_status("nonexistent") == "not_found"

    def test_get_analytics(self):
        result = self.pub.publish("Content")
        analytics = self.pub.get_analytics(result.post_id)
        assert "views" in analytics
        assert "likes" in analytics

    def test_schedule(self):
        result = self.pub.schedule("Content", scheduled_time=1234567890)
        assert result.success
        assert "scheduled_time" in result.metadata


# ── PluginManager Tests ──

class TestPluginManager:
    def setup_method(self):
        self.manager = PluginManager()
        self.manager.register("mock", MockPublisher)

    def test_register(self):
        self.manager.register("another", MockPublisher)
        assert self.manager.registry.is_registered("another")

    def test_authenticate(self):
        assert self.manager.authenticate("mock", {"token": "x"})

    def test_authenticate_fail(self):
        import pytest
        with pytest.raises(PluginNotFoundError):
            self.manager.authenticate("nonexistent", {})

    def test_publish(self):
        result = self.manager.publish("mock", "Hello world")
        assert result.success
        assert result.platform == "mock"

    def test_publish_with_media(self):
        result = self.manager.publish("mock", "Post", media_paths=["img.jpg"])
        assert result.success

    def test_edit(self):
        result = self.manager.publish("mock", "Original")
        edited = self.manager.edit("mock", result.post_id, "Edited")
        assert edited.success

    def test_delete(self):
        result = self.manager.publish("mock", "Delete me")
        assert self.manager.delete("mock", result.post_id)

    def test_get_post(self):
        result = self.manager.publish("mock", "Content")
        post = self.manager.get_post("mock", result.post_id)
        assert post is not None

    def test_get_status(self):
        result = self.manager.publish("mock", "Content")
        assert self.manager.get_status("mock", result.post_id) == "published"

    def test_get_analytics(self):
        result = self.manager.publish("mock", "Content")
        analytics = self.manager.get_analytics("mock", result.post_id)
        assert "views" in analytics

    def test_get_capabilities(self):
        caps = self.manager.get_capabilities("mock")
        assert caps.supports_images

    def test_supports(self):
        assert self.manager.supports("mock", "images")
        assert not self.manager.supports("mock", "nonexistent_feature")

    def test_find_platforms_with_feature(self):
        platforms = self.manager.find_platforms_with_feature("images")
        assert "mock" in platforms

    def test_get_all_capabilities(self):
        all_caps = self.manager.get_all_capabilities()
        assert "mock" in all_caps

    def test_not_found_error(self):
        import pytest
        with pytest.raises(PluginNotFoundError):
            self.manager.publish("nonexistent", "test")

    def test_operation_count(self):
        self.manager.publish("mock", "A")
        self.manager.publish("mock", "B")
        assert self.manager.operation_count == 2

    def test_multi_platform(self):
        self.manager.register("platform_a", MockPublisher)
        self.manager.register("platform_b", MockPublisher)
        r1 = self.manager.publish("platform_a", "Content A")
        r2 = self.manager.publish("platform_b", "Content B")
        assert r1.success and r2.success
        assert r1.success and r2.success
        assert r1.post_id != r2.post_id
