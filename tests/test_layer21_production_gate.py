"""Layer 21 production certification contract tests."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from layers.layer21_deployment import (
    BuildManager,
    Environment,
    EnvironmentManager,
    ReleaseManager,
    ReleaseStatus,
    StartupManager,
    StartupPhase,
)
from layers.layer21_deployment.modules.docker_engine.docker_deployment_manager import (
    DockerDeploymentManager,
)


def test_build_manager_executes_real_steps_and_fails_closed():
    calls = []
    def runner(args, timeout):
        calls.append((tuple(args), timeout))
        return (0, "PASS", "")
    manager = BuildManager(runner=runner, timeout=30)
    build = manager.create_build("6.0.0", ["python -m compileall -q layers"])
    result = manager.execute_build(build.build_id)
    assert result["status"] == "success"
    assert result["steps"][0]["status"] == "success"
    assert calls == [(("python", "-m", "compileall", "-q", "layers"), 30)]


def test_build_manager_marks_failed_command():
    manager = BuildManager(runner=lambda args, timeout: (1, "", "boom"))
    build = manager.create_build("6.0.0", ["python -m pytest -q"])
    result = manager.execute_build(build.build_id)
    assert result["status"] == "failed"
    assert result["steps"][0]["status"] == "failed"


def test_environment_secrets_are_not_exposed_by_status():
    manager = EnvironmentManager()
    manager.create(Environment.PRODUCTION)
    assert manager.set_variable(
        "production", "POSTGRES_PASSWORD", "super-secret", secret=True
    )
    assert manager.get_secret("production", "POSTGRES_PASSWORD") == "super-secret"
    status = manager.list_environments()[0]
    assert "super-secret" not in str(status)
    assert status["secrets_count"] == 1


def test_production_activation_requires_password():
    manager = EnvironmentManager()
    manager.create(Environment.PRODUCTION)
    with pytest.raises(ValueError):
        manager.activate("production")


def test_release_lifecycle_is_guarded():
    manager = ReleaseManager()
    release = manager.create_release("6.1.0")
    assert manager.release(release.release_id) is False
    assert manager.begin_testing(release.release_id) is True
    assert manager.release(release.release_id) is True
    assert manager.list_releases()[0]["status"] == ReleaseStatus.RELEASED.value
    assert manager.rollback(release.release_id) is True
    assert manager.get_current_version() == "0.0.0"


def test_startup_is_deterministic_and_fail_closed():
    manager = StartupManager()
    events = []
    manager.add_step("ready", StartupPhase.READY, lambda: events.append("ready"))
    manager.add_step("init", StartupPhase.INIT, lambda: events.append("init"))
    result = manager.startup()
    assert result["status"] == "success"
    assert events == ["init", "ready"]


def test_startup_required_failure_stops_pipeline():
    manager = StartupManager()
    manager.add_step("init", StartupPhase.INIT, lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    manager.add_step("ready", StartupPhase.READY, lambda: pytest.fail("must not run"))
    result = manager.startup()
    assert result["status"] == "failed"
    assert result["failed_step"] == "init"


def test_docker_verification_requires_health_not_only_running():
    DockerDeploymentManager._instance = None
    manager = DockerDeploymentManager()
    healthy = {
        "Status": "running",
        "Health": {"Status": "healthy"},
        "RestartCount": 0,
        "StartedAt": "2026-01-01T00:00:00Z",
    }
    def run(args, timeout=10):
        if args[:3] == ["docker", "--version",] or args[:3] == ["docker", "compose", "version"]:
            return 0, "Docker version test", ""
        if args[:3] == ["docker", "inspect", "--format={{json .State}}"]:
            return 0, __import__("json").dumps(healthy), ""
        if args[:2] == ["docker", "stats"]:
            return 0, "128MiB 1.0%", ""
        return 1, "", ""
    manager._run_command = run
    result = manager.verify_deployment()
    assert result["overall"] is True
    assert result["containers_running"] == result["containers_expected"] == 3


def test_docker_service_name_validation_blocks_argument_injection():
    DockerDeploymentManager._instance = None
    manager = DockerDeploymentManager()
    with pytest.raises(ValueError):
        manager.get_logs("aios;touch /tmp/pwned", 10)
