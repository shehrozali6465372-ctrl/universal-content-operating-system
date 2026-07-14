"""Tests for WorkflowEngine."""

from layers.layer02_research.modules.research_orchestrator.workflow_engine import WorkflowEngine, Workflow, WorkflowStep
from layers.layer02_research.modules.research_orchestrator.exceptions import WorkflowError


class TestWorkflowStep:
    def test_create(self):
        s = WorkflowStep("m1", ["m0"])
        assert s.name == "m1"
        assert s.dependencies == ["m0"]

    def test_to_dict(self):
        d = WorkflowStep("m1", ["m0"]).to_dict()
        assert d["name"] == "m1"


class TestWorkflow:
    def test_create(self):
        wf = Workflow("test", "Test workflow")
        assert wf.name == "test"

    def test_add_step(self):
        wf = Workflow("test")
        wf.add_step("m1").add_step("m2", ["m1"])
        assert len(wf.steps) == 2

    def test_add_duplicate_step(self):
        wf = Workflow("test")
        wf.add_step("m1")
        try:
            wf.add_step("m1")
            assert False, "Should have raised"
        except WorkflowError:
            pass

    def test_remove_step(self):
        wf = Workflow("test")
        wf.add_step("m1")
        assert wf.remove_step("m1") is True
        assert len(wf.steps) == 0

    def test_remove_nonexistent(self):
        wf = Workflow("test")
        assert wf.remove_step("nope") is False

    def test_get_step(self):
        wf = Workflow("test")
        wf.add_step("m1")
        assert wf.get_step("m1") is not None
        assert wf.get_step("nope") is None

    def test_get_module_order(self):
        wf = Workflow("test")
        wf.add_step("a").add_step("b").add_step("c")
        assert wf.get_module_order() == ["a", "b", "c"]

    def test_get_dependencies(self):
        wf = Workflow("test")
        wf.add_step("a").add_step("b", ["a"])
        deps = wf.get_dependencies()
        assert deps["b"] == ["a"]
        assert deps["a"] == []

    def test_get_root_modules(self):
        wf = Workflow("test")
        wf.add_step("a").add_step("b", ["a"])
        assert wf.get_root_modules() == ["a"]

    def test_get_leaf_modules(self):
        wf = Workflow("test")
        wf.add_step("a").add_step("b", ["a"])
        assert wf.get_leaf_modules() == ["b"]

    def test_validate_ok(self):
        wf = Workflow("test")
        wf.add_step("a").add_step("b", ["a"])
        assert wf.validate() == []

    def test_validate_missing_dep(self):
        wf = Workflow("test")
        wf.add_step("a", ["nonexistent"])
        errors = wf.validate()
        assert len(errors) > 0

    def test_to_dict(self):
        wf = Workflow("test", "desc")
        wf.add_step("a")
        d = wf.to_dict()
        assert d["name"] == "test"
        assert len(d["steps"]) == 1


class TestWorkflowEngine:
    def setup_method(self):
        self.we = WorkflowEngine()

    def test_has_default_workflow(self):
        assert "default_research" in self.we.list_workflows()

    def test_create_workflow(self):
        wf = self.we.create_workflow("custom", "My workflow")
        assert wf.name == "custom"

    def test_get_workflow(self):
        assert self.we.get_workflow("default_research") is not None
        assert self.we.get_workflow("nonexistent") is None

    def test_set_active_workflow(self):
        assert self.we.set_active_workflow("default_research") is True
        assert self.we.set_active_workflow("nonexistent") is False

    def test_get_active_workflow(self):
        self.we.set_active_workflow("default_research")
        wf = self.we.get_active_workflow()
        assert wf is not None

    def test_register_module(self):
        def dummy():
            pass
        self.we.register_module("m1", dummy)
        assert "m1" in self.we.list_registered_modules()

    def test_get_module_func(self):
        def dummy():
            pass
        self.we.register_module("m1", dummy)
        assert self.we.get_module_func("m1") is dummy
        assert self.we.get_module_func("nope") is None

    def test_default_workflow_has_modules(self):
        wf = self.we.get_workflow("default_research")
        assert len(wf.steps) >= 8
