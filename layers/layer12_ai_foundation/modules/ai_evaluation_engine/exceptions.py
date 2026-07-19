"""Custom exceptions for AI Evaluation Engine."""
from __future__ import annotations
class EvalError(Exception):
    """Base error for evaluation engine."""
class HallucinationDetected(EvalError): pass
class BiasDetected(EvalError): pass
class SafetyViolation(EvalError): pass
class QualityBelowThreshold(EvalError): pass
class EvaluationTimeout(EvalError): pass
