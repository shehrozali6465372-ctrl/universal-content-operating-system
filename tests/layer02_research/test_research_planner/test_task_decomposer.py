"""Tests for TaskDecomposer."""

from layers.layer02_research.modules.research_planner.task_decomposer import TaskDecomposer


class TestTaskDecomposer:
    def setup_method(self):
        self.decomposer = TaskDecomposer()

    def test_decompose_all_modules(self):
        tasks = self.decomposer.decompose("AI Jobs")
        assert len(tasks) > 0
        modules = {t.module for t in tasks}
        assert "trend_discovery" in modules
        assert "fact_verification" in modules

    def test_decompose_specific_modules(self):
        tasks = self.decomposer.decompose("AI", modules=["trend_discovery"])
        assert len(tasks) > 0
        assert all(t.module == "trend_discovery" for t in tasks)

    def test_decompose_empty_modules(self):
        tasks = self.decomposer.decompose("AI", modules=[])
        assert len(tasks) == 0

    def test_decompose_custom_tasks(self):
        custom = [{"name": "Custom task", "module": "custom", "priority": "HIGH"}]
        tasks = self.decomposer.decompose("AI", modules=[], custom_tasks=custom)
        assert len(tasks) == 1
        assert tasks[0].name == "Custom task"

    def test_decompose_minimal(self):
        tasks = self.decomposer.decompose_minimal("AI Jobs")
        modules = {t.module for t in tasks}
        # Should only contain critical modules
        assert "trend_discovery" in modules
        assert "fact_verification" in modules
        assert "knowledge_collector" in modules
        assert "topic_scoring" in modules

    def test_decompose_task_topic_in_name(self):
        tasks = self.decomposer.decompose("Crypto", modules=["trend_discovery"])
        for t in tasks:
            assert "Crypto" in t.name

    def test_add_template(self):
        new_tasks = [{"name": "New task", "module": "new_module", "priority": "LOW"}]
        self.decomposer.add_template("new_module", new_tasks)
        assert "new_module" in self.decomposer.get_modules()

    def test_get_modules(self):
        modules = self.decomposer.get_modules()
        assert "trend_discovery" in modules
        assert "fact_verification" in modules
        assert len(modules) >= 7

    def test_decompose_task_estimates(self):
        tasks = self.decomposer.decompose("AI", modules=["trend_discovery"])
        for t in tasks:
            assert t.estimated_time_min > 0
            assert t.estimated_api_calls >= 0
