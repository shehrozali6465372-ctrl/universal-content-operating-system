"""
Orchestrator Manager
Layer 2: Research Engine — Module 10

Main entry point for the Research Orchestrator:
- Plan → Execute → Checkpoint → Retry → Complete
- State management
- Metrics collection
- Resume from failure
"""

from typing import Any, Callable, Dict, List, Optional

from layers.layer02_research.modules.research_orchestrator.execution_context import ExecutionContext
from layers.layer02_research.modules.research_orchestrator.state_manager import StateManager
from layers.layer02_research.modules.research_orchestrator.checkpoint_manager import CheckpointManager
from layers.layer02_research.modules.research_orchestrator.failure_handler import FailureHandler
from layers.layer02_research.modules.research_orchestrator.metrics_collector import MetricsCollector
from layers.layer02_research.modules.research_orchestrator.pipeline_manager import PipelineManager, PipelineResult
from layers.layer02_research.modules.research_orchestrator.workflow_engine import WorkflowEngine
from layers.layer02_research.modules.research_orchestrator.retry_coordinator import RetryPolicy


class OrchestratorManager:
    """Main orchestrator for research workflows."""

    def __init__(self, retry_policy: Optional[RetryPolicy] = None):
        self.state_manager = StateManager()
        self.checkpoint_manager = CheckpointManager()
        self.failure_handler = FailureHandler(retry_policy)
        self.metrics_collector = MetricsCollector()
        self.workflow_engine = WorkflowEngine()
        self.pipeline_manager = PipelineManager(self.workflow_engine)
        self._executions: Dict[str, ExecutionContext] = {}
        self._execution_results: Dict[str, PipelineResult] = {}

    def create_execution(
        self,
        topic: str,
        workflow_name: str = "default_research",
        niche: str = "general",
    ) -> ExecutionContext:
        """Create a new research execution."""
        ctx = self.pipeline_manager.create_pipeline(topic, workflow_name, niche)
        self._executions[ctx.execution_id] = ctx
        self.state_manager.transition("created", "planned", f"Pipeline created for '{topic}'")
        return ctx

    def execute(
        self,
        context: ExecutionContext,
        module_funcs: Optional[Dict[str, Callable]] = None,
        custom_context: Optional[Dict] = None,
    ) -> PipelineResult:
        """Execute a research pipeline."""
        current = context.status
        if self.state_manager.can_transition(current, "running"):
            self.state_manager.transition(current, "running", "Starting execution")
        context.start()

        result = self.pipeline_manager.execute_pipeline(
            context, module_funcs, custom_context
        )

        # Save final checkpoint
        self.checkpoint_manager.save_checkpoint(
            context.execution_id,
            "__final__",
            state=context.to_dict(),
            completed_modules=context.completed_modules,
            confidence=context.overall_confidence,
        )

        # Record metrics
        self.metrics_collector.record_execution(context)
        for module in context.completed_modules:
            self.metrics_collector.record_module(
                module, success=True, confidence=context.overall_confidence
            )
        for module in context.failed_modules:
            self.metrics_collector.record_module(
                module, success=False, confidence=0.0
            )

        self._execution_results[context.execution_id] = result

        # Transition to final state
        current = context.status
        if result.success:
            if self.state_manager.can_transition(current, "completed"):
                self.state_manager.transition(current, "completed", "All modules succeeded")
        elif current not in ("cancelled", "completed", "failed"):
            if self.state_manager.can_transition(current, "failed"):
                self.state_manager.transition(current, "failed", "Some modules failed")

        return result

    def resume(
        self,
        execution_id: str,
        module_funcs: Optional[Dict[str, Callable]] = None,
    ) -> Optional[PipelineResult]:
        """Resume a failed/paused execution from last checkpoint."""
        checkpoint = self.checkpoint_manager.restore_from_checkpoint(execution_id)
        if not checkpoint:
            return None

        ctx = self._executions.get(execution_id)
        if not ctx:
            return None

        if ctx.status not in ("paused", "failed"):
            return None

        self.state_manager.transition(ctx.status, "resuming", "Resuming from checkpoint")
        ctx.resume()

        # Re-execute from checkpoint module onward
        result = self.execute(ctx, module_funcs)
        return result

    def pause(self, execution_id: str) -> bool:
        """Pause a running execution."""
        ctx = self._executions.get(execution_id)
        if not ctx or ctx.status != "running":
            return False

        self.state_manager.transition(ctx.status, "paused", "Manual pause")
        ctx.pause()

        # Save checkpoint
        self.checkpoint_manager.save_checkpoint(
            execution_id, ctx.current_module,
            state=ctx.to_dict(),
            completed_modules=ctx.completed_modules,
            confidence=ctx.overall_confidence,
        )
        return True

    def cancel(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        ctx = self._executions.get(execution_id)
        if not ctx:
            return False
        if self.state_manager.is_terminal(ctx.status):
            return False

        try:
            self.state_manager.transition(ctx.status, "cancelled", "Manual cancel")
        except Exception:
            pass

        ctx.cancel()
        return True

    def handle_module_failure(
        self,
        context: ExecutionContext,
        module: str,
        error: Exception,
        fallback_func: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Handle a failed module with retry/fallback logic."""
        # Save checkpoint before failure handling
        self.checkpoint_manager.save_checkpoint(
            context.execution_id, module,
            state=context.to_dict(),
            completed_modules=context.completed_modules,
            confidence=context.overall_confidence,
        )

        recovery = self.failure_handler.handle_failure(module, error, fallback_func)
        return recovery

    def get_execution(self, execution_id: str) -> Optional[ExecutionContext]:
        return self._executions.get(execution_id)

    def get_result(self, execution_id: str) -> Optional[PipelineResult]:
        return self._execution_results.get(execution_id)

    def list_executions(self, status: Optional[str] = None) -> List[ExecutionContext]:
        execs = list(self._executions.values())
        if status:
            execs = [e for e in execs if e.status == status]
        return execs

    def get_metrics(self) -> Dict:
        """Get aggregated metrics across all executions."""
        return {
            "module_stats": self.metrics_collector.get_all_stats(),
            "execution_summary": self.metrics_collector.get_execution_summary(),
            "slowest_modules": self.metrics_collector.get_slowest_modules(),
            "failure_counts": self.failure_handler.get_failure_counts(),
            "total_retries": self.failure_handler.retry_coordinator.get_total_retries(),
        }

    def register_module(self, name: str, func: Callable):
        """Register a module function with the workflow engine."""
        self.workflow_engine.register_module(name, func)

    def reset(self):
        """Clear all state."""
        self._executions.clear()
        self._execution_results.clear()
        self.state_manager.reset()
        self.failure_handler.reset()
        self.metrics_collector.reset()
        self.pipeline_manager.reset()
