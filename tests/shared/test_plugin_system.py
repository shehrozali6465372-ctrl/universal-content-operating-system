"""Tests for Plugin System."""

from layers.shared.plugin_system import PluginManager, Plugin, PluginMetadata


class FakePlugin(Plugin):
    def metadata(self):
        return PluginMetadata("fake", "1.0.0", "test", "A fake plugin", "research", ["trend"])

    def get_capabilities(self):
        return ["discover_trends", "analyze"]


class FakePlugin2(Plugin):
    def __init__(self):
        self.init_called = False
        self.activate_called = False
        self.deactivate_called = False

    def metadata(self):
        return PluginMetadata("fake2", "2.0.0", "test", "Another plugin", "publishing", ["post"])

    def get_capabilities(self):
        return ["publish"]

    def on_init(self):
        self.init_called = True

    def on_activate(self):
        self.activate_called = True

    def on_deactivate(self):
        self.deactivate_called = True


class TestPluginMetadata:
    def test_create(self):
        m = PluginMetadata("test", "1.0", "author", "desc", "cat", ["tag1"])
        assert m.name == "test"
        assert m.version == "1.0"

    def test_to_dict(self):
        d = PluginMetadata("test", "1.0", tags=["x"]).to_dict()
        assert d["name"] == "test"
        assert d["tags"] == ["x"]


class TestPluginManager:
    def setup_method(self):
        self.pm = PluginManager()

    def test_register(self):
        assert self.pm.register("fake", FakePlugin) is True

    def test_register_duplicate(self):
        self.pm.register("fake", FakePlugin)
        assert self.pm.register("fake", FakePlugin) is False

    def test_unregister(self):
        self.pm.register("fake", FakePlugin)
        assert self.pm.unregister("fake") is True
        assert self.pm.has_capability("discover_trends") is False

    def test_unregister_nonexistent(self):
        assert self.pm.unregister("nope") is False

    def test_activate(self):
        self.pm.register("fake", FakePlugin)
        assert self.pm.activate("fake") is True

    def test_activate_nonexistent(self):
        assert self.pm.activate("nope") is False

    def test_activate_already_active(self):
        self.pm.register("fake", FakePlugin)
        self.pm.activate("fake")
        assert self.pm.activate("fake") is False

    def test_deactivate(self):
        self.pm.register("fake", FakePlugin)
        self.pm.activate("fake")
        assert self.pm.deactivate("fake") is True

    def test_deactivate_not_active(self):
        self.pm.register("fake", FakePlugin)
        assert self.pm.deactivate("fake") is False

    def test_get_active_plugin(self):
        self.pm.register("fake", FakePlugin)
        self.pm.activate("fake")
        plugin = self.pm.get("fake")
        assert plugin is not None
        assert "discover_trends" in plugin.get_capabilities()

    def test_get_inactive_plugin(self):
        self.pm.register("fake", FakePlugin)
        assert self.pm.get("fake") is None

    def test_list_plugins(self):
        self.pm.register("a", FakePlugin)
        self.pm.register("b", FakePlugin2)
        assert len(self.pm.list_plugins()) == 2

    def test_list_active_only(self):
        self.pm.register("a", FakePlugin)
        self.pm.register("b", FakePlugin2)
        self.pm.activate("a")
        active = self.pm.list_plugins(active_only=True)
        assert active == ["a"]

    def test_list_by_category(self):
        self.pm.register("fake", FakePlugin)
        self.pm.register("fake2", FakePlugin2)
        research = self.pm.list_by_category("research")
        assert research == ["fake"]

    def test_list_by_capability(self):
        self.pm.register("fake", FakePlugin)
        self.pm.register("fake2", FakePlugin2)
        self.pm.activate("fake")
        self.pm.activate("fake2")
        publishers = self.pm.list_by_capability("publish")
        assert "fake2" in publishers

    def test_has_capability(self):
        self.pm.register("fake", FakePlugin)
        self.pm.activate("fake")
        assert self.pm.has_capability("discover_trends") is True
        assert self.pm.has_capability("nonexistent") is False

    def test_activate_all(self):
        self.pm.register("a", FakePlugin, priority=1)
        self.pm.register("b", FakePlugin2, priority=2)
        self.pm.activate_all()
        active = self.pm.list_plugins(active_only=True)
        assert len(active) == 2

    def test_deactivate_all(self):
        self.pm.register("a", FakePlugin)
        self.pm.activate_all()
        self.pm.deactivate_all()
        assert len(self.pm.list_plugins(active_only=True)) == 0

    def test_lifecycle_hooks(self):
        plugin = FakePlugin2()
        self.pm.register("f2", FakePlugin2)
        # The instance stored is the one created during registration
        stored = self.pm._plugins["f2"].instance
        self.pm.activate("f2")
        assert stored.activate_called is True
        self.pm.deactivate("f2")
        assert stored.deactivate_called is True

    def test_on_hook(self):
        activated = []
        self.pm.on("activated", lambda name: activated.append(name))
        self.pm.register("fake", FakePlugin)
        self.pm.activate("fake")
        assert "fake" in activated

    def test_get_metadata(self):
        self.pm.register("fake", FakePlugin)
        meta = self.pm.get_metadata("fake")
        assert meta is not None
        assert meta.name == "fake"

    def test_get_stats(self):
        self.pm.register("fake", FakePlugin)
        self.pm.register("fake2", FakePlugin2)
        self.pm.activate("fake")
        stats = self.pm.get_stats()
        assert stats["total_registered"] == 2
        assert stats["active"] == 1

    def test_reset(self):
        self.pm.register("fake", FakePlugin)
        self.pm.activate("fake")
        self.pm.reset()
        assert self.pm.list_plugins() == []
