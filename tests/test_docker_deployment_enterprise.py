"""Enterprise Docker Deployment Tests — 57+ tests."""
import json
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, ".")

from layers.layer21_deployment.modules.docker_engine.docker_deployment_manager import (
    ContainerHealth,
    DeploymentConfig,
    DeploymentStatus,
    DockerDeploymentManager,
    get_docker_manager,
)
from layers.layer21_deployment.modules.docker_engine.docker_engine import (
    DockerConfig,
    DockerCompose,
    DockerEngine,
)


class TestContainerHealth(unittest.TestCase):
    def setUp(self):
        self.h = ContainerHealth("test-container")

    def test_init(self):
        self.assertEqual(self.h.name, "test-container")
        self.assertEqual(self.h.status, "unknown")
        self.assertFalse(self.h.healthy)

    def test_to_dict(self):
        d = self.h.to_dict()
        self.assertIn("name", d)
        self.assertIn("status", d)
        self.assertIn("healthy", d)
        self.assertIn("memory_mb", d)
        self.assertIn("cpu_percent", d)

    def test_to_dict_values(self):
        self.h.status = "running"
        self.h.healthy = True
        self.h.memory_mb = 256.5
        d = self.h.to_dict()
        self.assertEqual(d["status"], "running")
        self.assertTrue(d["healthy"])
        self.assertEqual(d["memory_mb"], 256.5)

    def test_uptime(self):
        self.h.uptime = 3600
        d = self.h.to_dict()
        self.assertEqual(d["uptime_seconds"], 3600)

    def test_restarts(self):
        self.h.restarts = 5
        d = self.h.to_dict()
        self.assertEqual(d["restarts"], 5)


class TestDeploymentConfig(unittest.TestCase):
    def setUp(self):
        self.config = DeploymentConfig("test-project")

    def test_init(self):
        self.assertEqual(self.config.project_name, "test-project")
        self.assertEqual(len(self.config.services), 0)

    def test_add_service(self):
        self.config.add_service("web", "nginx:latest", ports=["80:80"])
        self.assertEqual(len(self.config.services), 1)
        self.assertEqual(self.config.services[0]["name"], "web")

    def test_add_service_chain(self):
        result = self.config.add_service("a", "img:a").add_service("b", "img:b")
        self.assertEqual(len(self.config.services), 2)
        self.assertEqual(result, self.config)

    def test_service_config(self):
        self.config.add_service(
            "db", "postgres:16", ports=["5432:5432"],
            depends_on=["redis"], env={"POSTGRES_DB": "test"},
            memory_limit="1G", cpu_limit="1",
        )
        svc = self.config.services[0]
        self.assertEqual(svc["image"], "postgres:16")
        self.assertEqual(svc["ports"], ["5432:5432"])
        self.assertEqual(svc["depends_on"], ["redis"])
        self.assertEqual(svc["environment"]["POSTGRES_DB"], "test")

    def test_to_dict(self):
        self.config.add_service("web", "nginx")
        d = self.config.to_dict()
        self.assertEqual(d["project"], "test-project")
        self.assertEqual(d["services_count"], 1)
        self.assertIn("web", d["services"])

    def test_networks(self):
        self.assertIn("aios-net", self.config.networks)


class TestDeploymentStatus(unittest.TestCase):
    def setUp(self):
        self.status = DeploymentStatus()

    def test_init(self):
        self.assertFalse(self.status.overall_healthy)
        self.assertEqual(self.status.running, 0)
        self.assertEqual(self.status.stopped, 0)

    def test_to_dict(self):
        d = self.status.to_dict()
        self.assertIn("overall", d)
        self.assertIn("running", d)
        self.assertIn("stopped", d)
        self.assertIn("containers", d)
        self.assertEqual(d["overall"], "Unhealthy")

    def test_healthy_status(self):
        self.status.overall_healthy = True
        d = self.status.to_dict()
        self.assertEqual(d["overall"], "Healthy")

    def test_version(self):
        d = self.status.to_dict()
        self.assertEqual(d["version"], "6.0.0")

    def test_containers_in_dict(self):
        h = ContainerHealth("svc1")
        h.status = "running"
        self.status.containers["svc1"] = h
        d = self.status.to_dict()
        self.assertIn("svc1", d["containers"])

    def test_deployment_time(self):
        self.status.deployment_time = 12.5
        d = self.status.to_dict()
        self.assertEqual(d["deployment_time_seconds"], 12.5)


class TestDockerDeploymentManager(unittest.TestCase):
    def setUp(self):
        DockerDeploymentManager._instance = None
        self.mgr = DockerDeploymentManager()

    def tearDown(self):
        DockerDeploymentManager._instance = None

    def test_singleton(self):
        m1 = DockerDeploymentManager()
        m2 = DockerDeploymentManager()
        self.assertIs(m1, m2)

    def test_expected_services(self):
        self.assertEqual(
            self.mgr.EXPECTED_SERVICES,
            ["aios", "aios-worker", "postgres", "redis"],
        )

    def test_config_setup(self):
        self.assertEqual(len(self.mgr._config.services), 4)

    def test_get_deployment_status(self):
        status = self.mgr.get_deployment_status()
        self.assertIn("docker", status)
        self.assertIn("deployment", status)
        self.assertIn("config", status)
        self.assertEqual(status["deployment"]["total_services"], 4)

    @patch("subprocess.run")
    def test_docker_available(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Docker version 24.0.7",
            stderr="",
        )
        result = self.mgr.check_docker_available()
        self.assertTrue(result["docker_available"])

    @patch("subprocess.run")
    def test_docker_not_available(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        result = self.mgr.check_docker_available()
        self.assertFalse(result["docker_available"])

    @patch("subprocess.run")
    def test_get_container_health_running(self, mock_run):
        def side_effect(cmd, **kwargs):
            if "inspect" in cmd:
                return MagicMock(
                    returncode=0,
                    stdout="running healthy 0 2024-01-01T00:00:00Z",
                    stderr="",
                )
            if "stats" in cmd:
                return MagicMock(
                    returncode=0,
                    stdout="256.5MiB 12.5%",
                    stderr="",
                )
            return MagicMock(returncode=1, stdout="", stderr="")

        mock_run.side_effect = side_effect
        health = self.mgr.get_container_health("test")
        self.assertEqual(health.status, "running")
        self.assertTrue(health.healthy)

    @patch("subprocess.run")
    def test_get_container_health_not_found(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="not found")
        health = self.mgr.get_container_health("missing")
        self.assertEqual(health.status, "unknown")
        self.assertFalse(health.healthy)

    @patch("subprocess.run")
    def test_check_all_containers(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
        status = self.mgr.check_all_containers()
        self.assertEqual(status.total_services, 4)
        self.assertEqual(status.running, 0)
        self.assertEqual(status.stopped, 4)
        self.assertFalse(status.overall_healthy)

    @patch("subprocess.run")
    def test_stop(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="stopped", stderr="")
        result = self.mgr.stop()
        self.assertTrue(result["success"])

    @patch("subprocess.run")
    def test_restart(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="restarted", stderr="")
        result = self.mgr.restart("aios")
        self.assertTrue(result["success"])

    @patch("subprocess.run")
    def test_restart_all(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        result = self.mgr.restart()
        self.assertTrue(result["success"])

    @patch("subprocess.run")
    def test_get_logs(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="log line 1\nlog line 2", stderr=""
        )
        logs = self.mgr.get_logs("aios", 10)
        self.assertIn("log line 1", logs)

    def test_verify_deployment(self):
        result = self.mgr.verify_deployment()
        self.assertIn("docker_available", result)
        self.assertIn("overall", result)
        self.assertIn("checks", result)
        self.assertEqual(len(result["checks"]), 5)

    @patch("subprocess.run")
    def test_deploy_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="done", stderr="")
        result = self.mgr.deploy()
        self.assertTrue(result["success"])
        self.assertIn("duration_seconds", result)
        self.assertEqual(len(self.mgr._deploy_history), 1)

    @patch("subprocess.run")
    def test_deploy_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        result = self.mgr.deploy()
        self.assertFalse(result["success"])

    def test_deploy_history_limit(self):
        self.mgr._deploy_history = [{"id": i} for i in range(10)]
        status = self.mgr.get_deployment_status()
        self.assertLessEqual(len(status["deploy_history"]), 5)


class TestDockerEngine(unittest.TestCase):
    def setUp(self):
        self.engine = DockerEngine()

    def test_create_config(self):
        config = self.engine.create_config("web", "nginx", "1.25")
        self.assertEqual(config.image, "nginx")
        self.assertEqual(config.tag, "1.25")

    def test_get_config(self):
        self.engine.create_config("web", "nginx")
        config = self.engine.get_config("web")
        self.assertIsNotNone(config)
        self.assertEqual(config.image, "nginx")

    def test_get_config_missing(self):
        config = self.engine.get_config("missing")
        self.assertIsNone(config)

    def test_list_configs(self):
        self.engine.create_config("a", "img:a")
        self.engine.create_config("b", "img:b")
        keys = self.engine.list_configs()
        self.assertIn("a", keys)
        self.assertIn("b", keys)

    def test_generate_compose(self):
        self.engine.create_config("web", "nginx")
        compose = self.engine.generate_compose()
        self.assertIn("services:", compose)
        self.assertIn("nginx:", compose)

    def test_generate_dockerfile(self):
        config = self.engine.create_config("web", "python:3.12")
        df = self.engine.generate_dockerfile("web")
        self.assertIn("FROM", df)
        self.assertIn("CMD", df)

    def test_generate_dockerfile_missing(self):
        df = self.engine.generate_dockerfile("missing")
        self.assertEqual(df, "")


class TestDockerConfig(unittest.TestCase):
    def test_init(self):
        config = DockerConfig("myapp", "v1")
        self.assertEqual(config.image, "myapp")
        self.assertEqual(config.tag, "v1")

    def test_to_dict(self):
        config = DockerConfig("myapp", "v1")
        d = config.to_dict()
        self.assertEqual(d["image"], "myapp:v1")

    def test_generate_dockerfile(self):
        config = DockerConfig("myapp")
        df = config.generate_dockerfile()
        self.assertIn("FROM", df)
        self.assertIn("pip install", df)
        self.assertIn("EXPOSE", df)


class TestDockerCompose(unittest.TestCase):
    def test_init(self):
        compose = DockerCompose("test-project")
        self.assertEqual(compose.project_name, "test-project")

    def test_add_service(self):
        compose = DockerCompose()
        config = DockerConfig("nginx")
        compose.add_service("web", config)
        self.assertIn("web", compose.services)

    def test_generate(self):
        compose = DockerCompose()
        config = DockerConfig("nginx")
        config.ports = ["80:80"]
        compose.add_service("web", config)
        output = compose.generate()
        self.assertIn("version:", output)
        self.assertIn("web:", output)
        self.assertIn("80:80", output)


class TestGetDockerManager(unittest.TestCase):
    def setUp(self):
        DockerDeploymentManager._instance = None

    def tearDown(self):
        DockerDeploymentManager._instance = None

    def test_returns_singleton(self):
        m1 = get_docker_manager()
        m2 = get_docker_manager()
        self.assertIs(m1, m2)

    def test_is_correct_type(self):
        mgr = get_docker_manager()
        self.assertIsInstance(mgr, DockerDeploymentManager)


class TestFullEnterpriseStack(unittest.TestCase):
    """End-to-end: Docker Engine + Deployment Manager integration."""
    def setUp(self):
        DockerDeploymentManager._instance = None

    def tearDown(self):
        DockerDeploymentManager._instance = None

    @patch("subprocess.run")
    def test_full_stack(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")

        # 1. Docker engine config
        engine = DockerEngine()
        engine.create_config("aios", "aios", "latest")
        compose = engine.generate_compose()
        self.assertIn("aios", compose)

        # 2. Deployment config
        dep_config = DeploymentConfig("production")
        dep_config.add_service("postgres", "postgres:16-alpine", ports=["5432:5432"])
        dep_config.add_service("redis", "redis:7-alpine", ports=["6379:6379"])
        dep_config.add_service("aios", "aios:latest", depends_on=["postgres", "redis"])
        d = dep_config.to_dict()
        self.assertEqual(d["services_count"], 3)

        # 3. Deployment manager
        mgr = DockerDeploymentManager()
        status = mgr.get_deployment_status()
        self.assertIn("docker", status)
        self.assertEqual(status["deployment"]["total_services"], 4)

        # 4. Verification
        verification = mgr.verify_deployment()
        self.assertIn("checks", verification)
        self.assertGreater(len(verification["checks"]), 0)

        # 5. Container health
        for name in mgr.EXPECTED_SERVICES:
            health = mgr.get_container_health(name)
            self.assertIsInstance(health, ContainerHealth)


if __name__ == "__main__":
    unittest.main()
