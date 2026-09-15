import os

from layers.layer07_publishing.modules.platform_plugin_manager.plugin_manager import PluginManager


def test_target_platform_adapters_are_registered():
    manager = PluginManager()
    platforms = set(manager.registry.list_platforms())
    assert {"facebook", "instagram", "pinterest", "youtube", "tiktok"}.issubset(platforms)


def test_unconfigured_real_adapters_do_not_claim_authentication():
    manager = PluginManager()
    for platform in ("pinterest", "youtube", "tiktok"):
        publisher = manager.registry.get_instance(platform)
        assert publisher is not None
        assert publisher.authenticate({}) is False


def test_capabilities_are_platform_specific():
    manager = PluginManager()
    assert manager.get_capabilities("youtube").supports_video
    assert manager.get_capabilities("tiktok").supports_video
    assert manager.get_capabilities("pinterest").supports_images
    assert manager.get_capabilities("instagram").supports_video
