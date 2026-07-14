"""Tests for Research Orchestrator exceptions."""

from layers.layer02_research.modules.research_orchestrator.exceptions import (
    OrchestratorError, WorkflowError, StateError,
    CheckpointError, RetryExhaustedError,
    ExecutionCancelledError, PipelineError,
)


class TestExceptions:
    def test_orchestrator_error(self):
        try:
            raise OrchestratorError("test")
        except OrchestratorError as e:
            assert str(e) == "test"

    def test_workflow_error(self):
        try:
            raise WorkflowError("wf")
        except OrchestratorError:
            pass

    def test_state_error(self):
        try:
            raise StateError("state")
        except OrchestratorError:
            pass

    def test_checkpoint_error(self):
        try:
            raise CheckpointError("cp")
        except OrchestratorError:
            pass

    def test_retry_exhausted(self):
        try:
            raise RetryExhaustedError("exhausted")
        except OrchestratorError:
            pass

    def test_execution_cancelled(self):
        try:
            raise ExecutionCancelledError("cancelled")
        except OrchestratorError:
            pass

    def test_pipeline_error(self):
        try:
            raise PipelineError("pipeline")
        except OrchestratorError:
            pass
