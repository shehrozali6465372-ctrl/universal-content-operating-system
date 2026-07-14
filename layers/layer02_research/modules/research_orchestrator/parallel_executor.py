"""
Parallel Executor
Layer 2: Research Engine — Module 10

Manages parallel execution of independent modules:
- Wave-based execution
- Dependency-aware scheduling
- Result aggregation
"""

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set

from layers.layer02_research.modules.research_planner.dependency_graph import DependencyGraph


class ExecutionResult:
    """Result of executing a single module."""

    __slots__ = ("module", "success", "result", "confidence", "duration_sec", "error")

    def __init__(self, module: str):
        self.module = module
        self.success = False
        self.result: Any = None
        self.confidence = 0.0
        self.duration_sec = 0.0
        self.error = ""

    def to_dict(self) -> dict:
        return {
            "module": self.module,
            "success": self.success,
            "confidence": self.confidence,
            "duration_sec": round(self.duration_sec, 3),
            "error": self.error,
        }


class ParallelExecutor:
    """Executes modules in parallel waves based on dependency graph."""

    def __init__(self):
        self._results: Dict[str, ExecutionResult] = {}

    def build_waves(
        self,
        module_order: List[str],
        dependencies: Optional[Dict[str, List[str]]] = None,
    ) -> List[List[str]]:
        """Build execution waves from module order and dependencies.

        Returns a list of waves, where each wave is a list of modules
        that can execute in parallel.
        """
        graph = DependencyGraph()
        for module in module_order:
            graph.add_node(module)

        if dependencies:
            for module, deps in dependencies.items():
                for dep in deps:
                    if dep in module_order and module in module_order:
                        graph.add_edge(dep, module)

        waves: List[List[str]] = []
        completed: Set[str] = set()

        while len(completed) < len(module_order):
            ready = graph.get_ready_nodes(completed)
            if not ready:
                # Remaining modules have unresolvable deps; add them individually
                remaining = [m for m in module_order if m not in completed]
                for m in remaining:
                    waves.append([m])
                    completed.add(m)
                break

            waves.append(ready)
            completed.update(ready)

        return waves

    def execute_wave(
        self,
        modules: List[str],
        module_funcs: Dict[str, Callable[..., Any]],
        context: Optional[Dict] = None,
    ) -> List[ExecutionResult]:
        """Execute a single wave of modules sequentially."""
        wave_results = []
        ctx = context or {}

        for module in modules:
            result = ExecutionResult(module)
            func = module_funcs.get(module)

            if func is None:
                result.error = f"No function registered for module '{module}'"
                wave_results.append(result)
                self._results[module] = result
                continue

            start = datetime.now(timezone.utc)
            try:
                result.result = func(**ctx)
                result.success = True
                result.confidence = getattr(result.result, "confidence", 0.8)
            except Exception as exc:
                result.error = str(exc)
            end = datetime.now(timezone.utc)
            result.duration_sec = (end - start).total_seconds()

            wave_results.append(result)
            self._results[module] = result

        return wave_results

    def execute_all(
        self,
        module_order: List[str],
        module_funcs: Dict[str, Callable[..., Any]],
        dependencies: Optional[Dict[str, List[str]]] = None,
        context: Optional[Dict] = None,
    ) -> Dict[str, ExecutionResult]:
        """Execute all modules in dependency-respecting waves."""
        waves = self.build_waves(module_order, dependencies)

        for wave in waves:
            self.execute_wave(wave, module_funcs, context)

        return dict(self._results)

    def get_results(self) -> Dict[str, ExecutionResult]:
        return dict(self._results)

    def get_result(self, module: str) -> Optional[ExecutionResult]:
        return self._results.get(module)

    def get_success_rate(self) -> float:
        if not self._results:
            return 0.0
        successful = sum(1 for r in self._results.values() if r.success)
        return round(successful / len(self._results), 3)

    def get_total_duration(self) -> float:
        return sum(r.duration_sec for r in self._results.values())

    def reset(self):
        self._results.clear()
