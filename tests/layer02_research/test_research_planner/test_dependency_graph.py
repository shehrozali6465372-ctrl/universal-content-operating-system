"""Tests for DependencyGraph."""

from layers.layer02_research.modules.research_planner.dependency_graph import DependencyGraph


class TestDependencyGraph:
    def setup_method(self):
        self.graph = DependencyGraph()

    def test_add_node(self):
        self.graph.add_node("a")
        assert self.graph.size() == 1

    def test_add_edge(self):
        self.graph.add_edge("a", "b")
        assert self.graph.size() == 2

    def test_remove_node(self):
        self.graph.add_edge("a", "b")
        self.graph.remove_node("a")
        assert self.graph.size() == 1
        assert self.graph.get_ready_nodes(set()) == ["b"]

    def test_remove_node_cleans_edges(self):
        self.graph.add_edge("a", "b")
        self.graph.remove_node("b")
        assert self.graph.get_dependents("a") == []

    def test_no_cycle(self):
        self.graph.add_edge("a", "b")
        self.graph.add_edge("b", "c")
        assert self.graph.has_cycle() is False

    def test_cycle_detection(self):
        self.graph.add_edge("a", "b")
        self.graph.add_edge("b", "c")
        self.graph.add_edge("c", "a")
        assert self.graph.has_cycle() is True

    def test_topological_sort(self):
        self.graph.add_edge("a", "b")
        self.graph.add_edge("b", "c")
        order = self.graph.topological_sort()
        assert order is not None
        assert order.index("a") < order.index("b")
        assert order.index("b") < order.index("c")

    def test_topological_sort_cycle_returns_none(self):
        self.graph.add_edge("a", "b")
        self.graph.add_edge("b", "a")
        assert self.graph.topological_sort() is None

    def test_topological_sort_empty(self):
        assert self.graph.topological_sort() == []

    def test_get_ready_nodes(self):
        self.graph.add_edge("a", "b")
        self.graph.add_edge("a", "c")
        ready = self.graph.get_ready_nodes(set())
        assert ready == ["a"]

    def test_get_ready_nodes_after_completion(self):
        self.graph.add_edge("a", "b")
        self.graph.add_edge("b", "c")
        ready = self.graph.get_ready_nodes({"a"})
        assert ready == ["b"]

    def test_get_ready_nodes_all_completed(self):
        self.graph.add_edge("a", "b")
        ready = self.graph.get_ready_nodes({"a", "b"})
        assert ready == []

    def test_get_dependents(self):
        self.graph.add_edge("a", "b")
        self.graph.add_edge("a", "c")
        deps = self.graph.get_dependents("a")
        assert "b" in deps
        assert "c" in deps

    def test_get_dependencies(self):
        self.graph.add_edge("a", "c")
        self.graph.add_edge("b", "c")
        deps = self.graph.get_dependencies("c")
        assert "a" in deps
        assert "b" in deps

    def test_depth_root(self):
        self.graph.add_edge("a", "b")
        assert self.graph.depth("a") == 0

    def test_depth_nested(self):
        self.graph.add_edge("a", "b")
        self.graph.add_edge("b", "c")
        assert self.graph.depth("c") == 2

    def test_size(self):
        self.graph.add_edge("a", "b")
        assert self.graph.size() == 2

    def test_duplicate_edges(self):
        self.graph.add_edge("a", "b")
        self.graph.add_edge("a", "b")
        assert self.graph.size() == 2
