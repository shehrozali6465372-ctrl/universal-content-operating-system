"""Dependency-aware executor for Layer 02 research modules."""
from datetime import datetime, timezone
from math import isfinite
from typing import Any, Callable, Dict, List, Optional, Set

from layers.layer02_research.modules.research_planner.exceptions import DependencyError
from layers.layer02_research.modules.research_planner.dependency_graph import DependencyGraph


def _serializable_result(value: Any, depth: int = 0) -> Any:
    """Keep module outputs JSON-safe so agent results preserve actual findings."""
    if depth > 20:
        return {"type": type(value).__name__, "truncated": True}
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if isfinite(value) else None
    if isinstance(value, dict):
        return {str(key): _serializable_result(item, depth + 1) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serializable_result(item, depth + 1) for item in value]
    if isinstance(value, set):
        return [_serializable_result(item, depth + 1) for item in sorted(value, key=str)]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        try:
            return _serializable_result(value.to_dict(), depth + 1)
        except Exception:
            return {"type": type(value).__name__, "serializable": False}
    if hasattr(value, "isoformat") and callable(value.isoformat):
        try:
            return value.isoformat()
        except Exception:
            pass
    return {"type": type(value).__name__, "serializable": False}


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
            "result": _serializable_result(self.result),
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

        module_set = set(module_order)
        if len(module_set) != len(module_order):
            raise DependencyError("module_order contains duplicate module names")

        if dependencies:
            unknown_modules = set(dependencies) - module_set
            if unknown_modules:
                raise DependencyError(
                    f"Dependencies declared for unknown modules: {sorted(unknown_modules)}"
                )
            for module, deps in dependencies.items():
                unknown_deps = set(deps) - module_set
                if unknown_deps:
                    raise DependencyError(
                        f"Module '{module}' depends on unknown module: {sorted(unknown_deps)}"
                    )
                for dep in deps:
                    if dep == module:
                        raise DependencyError(
                            f"Module '{module}' cannot depend on itself"
                        )
                    graph.add_edge(dep, module)

        waves: List[List[str]] = []
        completed: Set[str] = set()

        while len(completed) < len(module_order):
            ready = graph.get_ready_nodes(completed)
            if not ready:
                remaining = [m for m in module_order if m not in completed]
                raise DependencyError(
                    f"Dependency cycle detected among modules: {remaining}"
                )

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
                raw_confidence = (
                    result.result.get("confidence", 0.0)
                    if isinstance(result.result, dict)
                    else getattr(result.result, "confidence", 0.0)
                )
                result.confidence = float(raw_confidence)
                if not isfinite(result.confidence) or not 0.0 <= result.confidence <= 1.0:
                    raise ValueError("module confidence must be finite and between 0 and 1")
                result.success = True
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
