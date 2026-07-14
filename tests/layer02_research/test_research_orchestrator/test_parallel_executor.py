"""Tests for ParallelExecutor."""

from layers.layer02_research.modules.research_orchestrator.parallel_executor import ParallelExecutor, ExecutionResult


class TestExecutionResult:
    def test_create(self):
        r = ExecutionResult("m1")
        assert r.module == "m1"
        assert r.success is False

    def test_to_dict(self):
        r = ExecutionResult("m1")
        r.success = True
        r.confidence = 0.9
        d = r.to_dict()
        assert d["module"] == "m1"
        assert d["success"] is True


class TestParallelExecutor:
    def setup_method(self):
        self.pe = ParallelExecutor()

    def test_build_waves_linear(self):
        waves = self.pe.build_waves(["a", "b", "c"])
        # Without deps, all are independent -> 1 wave
        assert len(waves) == 1
        assert set(waves[0]) == {"a", "b", "c"}

    def test_build_waves_with_deps(self):
        waves = self.pe.build_waves(
            ["a", "b", "c"],
            dependencies={"b": ["a"], "c": ["a"]},
        )
        assert len(waves) == 2  # a first, then b+c

    def test_build_waves_no_deps(self):
        waves = self.pe.build_waves(["a", "b", "c"])
        # Without explicit deps, all are independent -> 1 wave
        assert len(waves) == 1
        assert set(waves[0]) == {"a", "b", "c"}

    def test_execute_wave(self):
        def func_a():
            return "result_a"
        def func_b():
            return "result_b"
        funcs = {"a": func_a, "b": func_b}
        results = self.pe.execute_wave(["a", "b"], funcs)
        assert len(results) == 2
        assert all(r.success for r in results)

    def test_execute_wave_with_error(self):
        def good():
            return "ok"
        def bad():
            raise ValueError("fail")
        funcs = {"a": good, "b": bad}
        results = self.pe.execute_wave(["a", "b"], funcs)
        assert results[0].success is True
        assert results[1].success is False

    def test_execute_wave_missing_func(self):
        results = self.pe.execute_wave(["missing"], {})
        assert results[0].success is False
        assert "No function" in results[0].error

    def test_execute_all(self):
        def func(name="topic"):
            return f"done_{name}"
        funcs = {"a": func, "b": func, "c": func}
        results = self.pe.execute_all(["a", "b", "c"], funcs)
        assert len(results) == 3

    def test_get_success_rate(self):
        def good():
            return "ok"
        def bad():
            raise ValueError("fail")
        funcs = {"a": good, "b": bad}
        self.pe.execute_all(["a", "b"], funcs)
        rate = self.pe.get_success_rate()
        assert rate == 0.5

    def test_get_success_rate_empty(self):
        assert self.pe.get_success_rate() == 0.0

    def test_get_total_duration(self):
        def ok():
            return "ok"
        self.pe.execute_all(["a"], {"a": ok})
        assert self.pe.get_total_duration() >= 0

    def test_get_result(self):
        def ok():
            return "ok"
        self.pe.execute_all(["a"], {"a": ok})
        r = self.pe.get_result("a")
        assert r is not None
        assert r.success is True

    def test_reset(self):
        def ok():
            return "ok"
        self.pe.execute_all(["a"], {"a": ok})
        self.pe.reset()
        assert self.pe.get_results() == {}
