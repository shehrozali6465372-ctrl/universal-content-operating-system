"""Exceptions for universal orchestrator."""
from __future__ import annotations

class OrchestratorError(Exception): """Base error."""
class RoutingError(OrchestratorError): """Routing failed."""
class TransactionCoordError(OrchestratorError): """Transaction coordination failed."""
class CacheCoordError(OrchestratorError): """Cache coordination failed."""
class MigrationError(OrchestratorError): """Migration failed."""
class OptimizationError(OrchestratorError): """Optimization failed."""
class ConsistencyError(OrchestratorError): """Consistency check failed."""
