"""Cross-layer production architecture invariants.

These checks protect the frozen ownership boundaries. They are intentionally
static/structural: runtime/provider certification is performed by dedicated
gates and must not be inferred from source presence.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYERS = ROOT / "layers"


def _python_files():
    return [p for p in LAYERS.rglob("*.py") if "__pycache__" not in p.parts]


def _imports(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def test_l11_is_not_used_as_a_second_async_runtime_by_other_layers():
    """L11 is the integrations boundary; L15 owns async execution."""
    forbidden_prefixes = (
        "layers.layer11_async_runtime.modules.async_",
        "layers.layer11_async_runtime.modules.background_",
        "layers.layer11_async_runtime.modules.concurrent_",
        "layers.layer11_async_runtime.modules.distributed_",
        "layers.layer11_async_runtime.modules.event_loop_",
    )
    violations = []
    for path in _python_files():
        if "layers/layer11_async_runtime/" in path.as_posix():
            continue
        for module in _imports(path):
            if module.startswith(forbidden_prefixes):
                violations.append(f"{path}: {module}")
    assert not violations, "non-canonical L11 runtime imports detected:\n" + "\n".join(violations)


def test_production_durable_execution_has_one_owner():
    durable = ROOT / "layers" / "layer15_async_runtime" / "modules" / "durable_execution" / "durable_execution.py"
    source = durable.read_text(encoding="utf-8")
    assert "class DurableExecutionStore" in source
    assert "class DurableWorker" in source
    assert "requires canonical PostgreSQL" in source
    assert "FOR UPDATE SKIP LOCKED" in source


def test_l13_schema_uses_one_canonical_partial_dedupe_index():
    schema = (ROOT / "layers" / "layer13_persistence" / "modules" / "postgresql" / "migrations" / "schema.py").read_text(encoding="utf-8")
    assert '"dedupe_key VARCHAR(512) UNIQUE' not in schema
    assert "uq_durable_tasks_dedupe" in schema
    assert "DROP CONSTRAINT IF EXISTS durable_tasks_dedupe_key_key" in schema


def test_l07_production_publication_separates_provider_effect_from_intent():
    ledger = (ROOT / "layers" / "layer07_publishing" / "modules" / "publisher_engine" / "publisher_manager.py").read_text(encoding="utf-8")
    assert "record_provider_result" in ledger
    assert "get_provider_effect" in ledger
    assert "external_post_id" in ledger
    assert "OUTCOME_UNKNOWN" in ledger
    assert "reconciliation required" in ledger


def test_l14_production_pipeline_requires_server_authoritative_mode_and_workflow_identity():
    pipeline = (ROOT / "layers" / "layer14_enterprise_integration" / "modules" / "master_orchestrator" / "production_pipeline.py").read_text(encoding="utf-8")
    assert "effective_publish_mode" in pipeline
    assert "workflow_id is required for production publication" in pipeline
    assert 'request.idempotency_key = f"ucos:{account_id}:{req.platform}:{workflow_id}"' in pipeline
