"""Tests for DI Container."""

from layers.shared.di_container import Container, ServiceNotFoundError, CircularDependencyError


class TestContainer:
    def setup_method(self):
        self.c = Container()

    def test_register_and_resolve(self):
        self.c.register("greeting", lambda: "hello")
        assert self.c.resolve("greeting") == "hello"

    def test_resolve_not_found(self):
        try:
            self.c.resolve("nonexistent")
            assert False, "Should have raised"
        except ServiceNotFoundError:
            pass

    def test_singleton(self):
        self.c.register("counter", lambda: {"count": 0}, singleton=True)
        a = self.c.resolve("counter")
        b = self.c.resolve("counter")
        assert a is b

    def test_transient(self):
        self.c.register("counter", lambda: {"count": 0}, singleton=False)
        a = self.c.resolve("counter")
        b = self.c.resolve("counter")
        assert a is not b

    def test_register_instance(self):
        self.c.register_instance("config", {"debug": True})
        assert self.c.resolve("config") == {"debug": True}

    def test_register_type(self):
        class MyService:
            def __init__(self):
                self.value = 42
        self.c.register_type("svc", MyService)
        svc = self.c.resolve("svc")
        assert svc.value == 42

    def test_has(self):
        self.c.register("a", lambda: 1)
        assert self.c.has("a") is True
        assert self.c.has("b") is False

    def test_is_resolved(self):
        self.c.register("a", lambda: 1, singleton=True)
        assert self.c.is_resolved("a") is False
        self.c.resolve("a")
        assert self.c.is_resolved("a") is True

    def test_circular_dependency(self):
        self.c.register("a", lambda: self.c.resolve("b"))
        self.c.register("b", lambda: self.c.resolve("a"))
        try:
            self.c.resolve("a")
            assert False, "Should have raised"
        except CircularDependencyError:
            pass

    def test_tags(self):
        self.c.register("x", lambda: 1, tags=["cache"])
        self.c.register("y", lambda: 2, tags=["cache"])
        self.c.register("z", lambda: 3, tags=["db"])
        cached = self.c.get_by_tag("cache")
        assert len(cached) == 2

    def test_get_tags(self):
        self.c.register("a", lambda: 1, tags=["x", "y"])
        self.c.register("b", lambda: 2, tags=["y", "z"])
        tags = self.c.get_tags()
        assert tags == {"x", "y", "z"}

    def test_get_registered_names(self):
        self.c.register("a", lambda: 1)
        self.c.register("b", lambda: 2)
        names = self.c.get_registered_names()
        assert "a" in names
        assert "b" in names

    def test_reset(self):
        self.c.register("a", lambda: 1)
        self.c.reset()
        assert self.c.get_registered_names() == []

    def test_child_container(self):
        self.c.register("parent_val", lambda: 10)
        child = self.c.child()
        assert child.resolve("parent_val") == 10
        child.register("child_val", lambda: 20)
        # Parent doesn't have child's service
        assert self.c.has("child_val") is False

    def test_chainable_register(self):
        result = self.c.register("a", lambda: 1).register("b", lambda: 2)
        assert result is self.c

    def test_repr(self):
        self.c.register("a", lambda: 1)
        assert "1" in repr(self.c)
