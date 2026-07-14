"""
Workflow Engine
Layer 2: Research Engine — Module 10

Defines and manages research workflows:
- Workflow definitions
- Module registration
- Pipeline configuration
"""

from typing import Callable, Dict, List, Optional, Set

from layers.layer02_research.modules.research_orchestrator.exceptions import WorkflowError


# Default research pipeline: ordered list of (module_name, dependencies)
DEFAULT_RESEARCH_PIPELINE: List[tuple] = [
    ("trend_discovery", []),
    ("topic_intelligence", ["trend_discovery"]),
    ("competitor_analysis", ["trend_discovery"]),
    ("audience_research", ["topic_intelligence"]),
    ("knowledge_collector", ["topic_intelligence"]),
    ("fact_verification", ["knowledge_collector"]),
    ("research_memory", ["fact_verification"]),
    ("topic_scoring", ["research_memory", "competitor_analysis", "audience_research"]),
]


class WorkflowStep:
    """A single step in a workflow."""

    __slots__ = ("name", "dependencies", "config")

    def __init__(self, name: str, dependencies: Optional[List[str]] = None, config: Optional[Dict] = None):
        self.name = name
        self.dependencies = dependencies or []
        self.config = config or {}

    def to_dict(self) -> dict:
        return {"name": self.name, "dependencies": self.dependencies, "config": self.config}


class Workflow:
    """A complete research workflow definition."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.steps: List[WorkflowStep] = []
        self._step_names: Set[str] = set()

    def add_step(self, name: str, dependencies: Optional[List[str]] = None, config: Optional[Dict] = None) -> "Workflow":
        """Add a step to the workflow. Chainable."""
        if name in self._step_names:
            raise WorkflowError(f"Step '{name}' already exists in workflow '{self.name}'")

        step = WorkflowStep(name, dependencies, config)
        self.steps.append(step)
        self._step_names.add(name)
        return self

    def remove_step(self, name: str) -> bool:
        """Remove a step by name."""
        for i, step in enumerate(self.steps):
            if step.name == name:
                self.steps.pop(i)
                self._step_names.discard(name)
                return True
        return False

    def get_step(self, name: str) -> Optional[WorkflowStep]:
        for step in self.steps:
            if step.name == name:
                return step
        return None

    def get_module_order(self) -> List[str]:
        """Get ordered list of module names."""
        return [step.name for step in self.steps]

    def get_dependencies(self) -> Dict[str, List[str]]:
        """Get dependency map."""
        return {step.name: step.dependencies for step in self.steps}

    def get_root_modules(self) -> List[str]:
        """Get modules with no dependencies (entry points)."""
        return [step.name for step in self.steps if not step.dependencies]

    def get_leaf_modules(self) -> List[str]:
        """Get modules that nothing else depends on."""
        all_deps: Set[str] = set()
        for step in self.steps:
            all_deps.update(step.dependencies)
        return [step.name for step in self.steps if step.name not in all_deps]

    def validate(self) -> List[str]:
        """Validate workflow. Returns list of error messages."""
        errors = []
        all_names = self._step_names

        for step in self.steps:
            for dep in step.dependencies:
                if dep not in all_names:
                    errors.append(f"Step '{step.name}' depends on unknown step '{dep}'")

        return errors

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
        }


class WorkflowEngine:
    """Manages workflow definitions and module registrations."""

    def __init__(self):
        self._workflows: Dict[str, Workflow] = {}
        self._module_registry: Dict[str, Callable] = {}
        self._active_workflow: Optional[str] = None

        # Register the default pipeline
        self.register_default_workflow()

    def register_default_workflow(self):
        """Register the default research pipeline."""
        wf = Workflow("default_research", "Standard research pipeline")
        for module_name, deps in DEFAULT_RESEARCH_PIPELINE:
            wf.add_step(module_name, deps)
        self._workflows["default_research"] = wf

    def create_workflow(self, name: str, description: str = "") -> Workflow:
        """Create and register a new workflow."""
        wf = Workflow(name, description)
        self._workflows[name] = wf
        return wf

    def get_workflow(self, name: str) -> Optional[Workflow]:
        return self._workflows.get(name)

    def set_active_workflow(self, name: str) -> bool:
        if name in self._workflows:
            self._active_workflow = name
            return True
        return False

    def get_active_workflow(self) -> Optional[Workflow]:
        if self._active_workflow:
            return self._workflows.get(self._active_workflow)
        return None

    def register_module(self, name: str, func: Callable):
        """Register a callable for a module."""
        self._module_registry[name] = func

    def get_module_func(self, name: str) -> Optional[Callable]:
        return self._module_registry.get(name)

    def get_module_funcs(self) -> Dict[str, Callable]:
        return dict(self._module_registry)

    def list_workflows(self) -> List[str]:
        return list(self._workflows.keys())

    def list_registered_modules(self) -> List[str]:
        return list(self._module_registry.keys())
