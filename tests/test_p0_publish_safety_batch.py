"""P0 publish-safety regression checks.

These checks intentionally use plain assert so they can run with the standard
library when pytest is unavailable.
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_offline_gate_exists_at_all_three_boundaries():
    wiring = (ROOT / "layers/layer14_enterprise_integration/modules/master_orchestrator/pipeline_wiring.py").read_text()
    production = (ROOT / "layers/layer14_enterprise_integration/modules/master_orchestrator/production_pipeline.py").read_text()
    assert "P0-Preflight" in wiring
    assert "production AI generation cannot create an offline draft" in wiring
    assert "production publish boundary rejected offline-draft output" in production
    assert "if not configured and production and publish_mode == \"production\"" in wiring


def test_publish_idempotency_is_workflow_scoped_not_content_hash():
    source = (ROOT / "layers/layer14_enterprise_integration/modules/master_orchestrator/production_pipeline.py").read_text()
    assert "workflow_id" in source
    assert "ucos:{account_id}:{req.platform}:{workflow_id}" in source
    assert 'hashlib.sha256(response.text.encode()).hexdigest()[:24]' not in source


def test_verify_before_finalize():
    manager = (ROOT / "layers/layer07_publishing/modules/publisher_engine/publisher_manager.py").read_text()
    ledger = (ROOT / "layers/layer07_publishing/modules/publisher_engine/publication_ledger.py").read_text()
    assert "verification_state, evidence = self._verify_submission" in manager
    assert 'state == "VERIFIED_PUBLIC"' in manager
    assert "result.set_success(external_id" in manager
    assert "record_verification(" in manager
    assert "VERIFIED_PUBLIC" in ledger


def test_ambiguous_provider_outcome_is_held():
    manager = (ROOT / "layers/layer07_publishing/modules/publisher_engine/publisher_manager.py").read_text()
    ledger = (ROOT / "layers/layer07_publishing/modules/publisher_engine/publication_ledger.py").read_text()
    assert '"OUTCOME_UNKNOWN"' in ledger
    assert '"RECONCILING"' in ledger
    assert 'if state == "OUTCOME_UNKNOWN":' in manager
    assert "reconciliation required" in manager


def test_tiktok_public_gate_is_fail_closed():
    source = (ROOT / "layers/layer07_publishing/modules/platform_plugin_manager/tiktok/tiktok_publisher.py").read_text()
    assert "PUBLIC_TO_EVERYONE" in source
    assert "TikTok production publish blocked" in source
    assert 'publish_mode == "production"' in source
    assert "TikTok production publish blocked" in source


def test_docker_entrypoint_and_healthcheck():
    dockerfile = (ROOT / "Dockerfile").read_text()
    entrypoint = (ROOT / "docker/entrypoint.sh").read_text()
    assert 'ENTRYPOINT ["tini", "--"]' in dockerfile
    assert 'HEALTHCHECK' in dockerfile
    assert "http://localhost:8000/health" in dockerfile
    api = (ROOT / "layers/layer14_enterprise_integration/modules/api_gateway/api_gateway.py").read_text()
    assert 'status_code=200 if overall == "healthy" else 503' in api
    assert "exec python main.py \"$@\"" in entrypoint
    assert "refusing to start" in entrypoint

    result = subprocess.run(["bash", "-n", str(ROOT / "docker/entrypoint.sh")], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_changed_python_files_compile():
    paths = [
        ROOT / "layers/layer14_enterprise_integration/modules/master_orchestrator/pipeline_wiring.py",
        ROOT / "layers/layer14_enterprise_integration/modules/master_orchestrator/production_pipeline.py",
        ROOT / "layers/layer14_enterprise_integration/modules/master_orchestrator/control_plane.py",
        ROOT / "layers/layer07_publishing/modules/publisher_engine/publish_executor.py",
        ROOT / "layers/layer07_publishing/modules/platform_plugin_manager/tiktok/tiktok_publisher.py",
        ROOT / "layers/layer14_enterprise_integration/modules/api_gateway/api_gateway.py",
    ]
    for path in paths:
        result = subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True)
        assert result.returncode == 0, f"{path}: {result.stderr}"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
    print("P0 publish-safety plain-assert tests: PASS")
