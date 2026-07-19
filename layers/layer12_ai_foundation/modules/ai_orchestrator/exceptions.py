"""Custom exceptions for AI Orchestrator."""
from __future__ import annotations
class OrchestratorError(Exception): pass
class PipelineError(OrchestratorError): pass
class RoutingError(OrchestratorError): pass
class ExecutionError(OrchestratorError): pass
class TimeoutError(OrchestratorError): pass
class StateError(OrchestratorError): pass
class ResourceError(OrchestratorError): pass
