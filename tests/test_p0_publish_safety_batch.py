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
    source = (ROOT / "layers/layer14_enterprise_integration/modules/master_orchestrator/production_pipeline.py").read_text()
    assert "verified = self._verify_public_submission" in source
    assert "guard.finalize(reservation.reservation_id, result.post_id)" in source
    assert source.index("verified = self._verify_public_submission") < source.index("guard.finalize(reservation.reservation_id, result.post_id)")


def test_ambiguous_provider_outcome_is_held():
    executor = (ROOT / "layers/layer07_publishing/modules/publisher_engine/publish_executor.py").read_text()
    production = (ROOT / "layers/layer14_enterprise_integration/modules/master_orchestrator/production_pipeline.py").read_text()
    assert '"outcome": "unknown"' in executor
    assert 'metadata.get("outcome") == "unknown"' in production

    sys.path.insert(0, str(ROOT))
    from layers.layer07_publishing.modules.publisher_engine.content_repetition_guard import ContentRepetitionGuard

    db = ROOT / "data" / "p0-test-history.sqlite3"
    try:
        if db.exists():
            db.unlink()
        guard = ContentRepetitionGuard(str(db))
        decision = guard.reserve(account_id="p0-test", platform="facebook", content="unique ambiguous outcome test")
        assert decision.allowed
        guard.mark_pending(decision.reservation_id, "outcome-unknown")
        guard.release(decision.reservation_id)
        assert len(guard.pending("p0-test")) == 1
    finally:
        if db.exists():
            db.unlink()


def test_tiktok_public_gate_is_fail_closed():
    source = (ROOT / "layers/layer07_publishing/modules/platform_plugin_manager/tiktok/tiktok_publisher.py").read_text()
    assert "PUBLIC_TO_EVERYONE" in source
    assert "TikTok production publish blocked" in source
    assert "else (options[0]" not in source
    assert "SELF_ONLY" not in source


def test_docker_entrypoint_and_healthcheck():
    dockerfile = (ROOT / "Dockerfile").read_text()
    entrypoint = (ROOT / "docker/entrypoint.sh").read_text()
    assert 'ENTRYPOINT ["tini", "--"]' in dockerfile
    assert 'HEALTHCHECK' in dockerfile
    assert "http://localhost:8000/health" in dockerfile
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
    ]
    for path in paths:
        result = subprocess.run([sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True)
        assert result.returncode == 0, f"{path}: {result.stderr}"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
    print("P0 publish-safety plain-assert tests: PASS")
