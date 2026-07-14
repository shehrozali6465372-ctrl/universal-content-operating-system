"""
Research Orchestrator Module
Layer 2: Research Engine — Module 10

Conductor for the entire research pipeline:
- Workflow engine and pipeline management
- State machine with valid transitions
- Checkpoint/resume for crash recovery
- Parallel execution of independent modules
- Retry with exponential backoff
- Failure classification and recovery
- Metrics collection and reporting
"""

from layers.layer02_research.modules.research_orchestrator.orchestrator_manager import OrchestratorManager
from layers.layer02_research.modules.research_orchestrator.execution_context import ExecutionContext
from layers.layer02_research.modules.research_orchestrator.state_manager import StateManager
from layers.layer02_research.modules.research_orchestrator.checkpoint_manager import CheckpointManager
from layers.layer02_research.modules.research_orchestrator.retry_coordinator import RetryCoordinator, RetryPolicy
from layers.layer02_research.modules.research_orchestrator.failure_handler import FailureHandler
from layers.layer02_research.modules.research_orchestrator.parallel_executor import ParallelExecutor, ExecutionResult
from layers.layer02_research.modules.research_orchestrator.metrics_collector import MetricsCollector, ModuleMetrics
from layers.layer02_research.modules.research_orchestrator.workflow_engine import WorkflowEngine, Workflow
from layers.layer02_research.modules.research_orchestrator.pipeline_manager import PipelineManager, PipelineResult
from layers.layer02_research.modules.research_orchestrator.exceptions import (
    OrchestratorError, WorkflowError, StateError,
    CheckpointError, RetryExhaustedError,
    ExecutionCancelledError, PipelineError,
)

__all__ = [
    "OrchestratorManager",
    "ExecutionContext",
    "StateManager",
    "CheckpointManager",
    "RetryCoordinator",
    "RetryPolicy",
    "FailureHandler",
    "ParallelExecutor",
    "ExecutionResult",
    "MetricsCollector",
    "ModuleMetrics",
    "WorkflowEngine",
    "Workflow",
    "PipelineManager",
    "PipelineResult",
    "OrchestratorError",
    "WorkflowError",
    "StateError",
    "CheckpointError",
    "RetryExhaustedError",
    "ExecutionCancelledError",
    "PipelineError",
]
