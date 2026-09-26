"""Production Docker deployment, health verification, and safe command orchestration."""
from __future__ import annotations

import json
import re
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")


class ContainerHealth:
    __slots__ = (
        "name", "status", "healthy", "uptime", "restarts",
        "memory_mb", "cpu_percent", "last_check",
    )

    def __init__(self, name: str) -> None:
        self.name = name
        self.status = "unknown"
        self.healthy = False
        self.uptime = 0.0
        self.restarts = 0
        self.memory_mb = 0.0
        self.cpu_percent = 0.0
        self.last_check = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "healthy": self.healthy,
            "uptime_seconds": round(self.uptime, 1),
            "restarts": self.restarts,
            "memory_mb": round(self.memory_mb, 1),
            "cpu_percent": round(self.cpu_percent, 1),
        }


class DeploymentConfig:
    __slots__ = (
        "project_name", "services", "volumes", "networks",
        "env_file", "compose_file",
    )

    def __init__(self, project_name: str = "aios") -> None:
        if not _SAFE_NAME.fullmatch(project_name):
            raise ValueError("Invalid project name")
        self.project_name = project_name
        self.services: List[Dict[str, Any]] = []
        self.volumes: List[str] = []
        self.networks = ["aios-net"]
        self.env_file = ".env"
        self.compose_file = "docker-compose.yml"

    def add_service(
        self,
        name: str,
        image: str,
        ports: Optional[List[str]] = None,
        volumes: Optional[List[str]] = None,
        depends_on: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        healthcheck: Optional[str] = None,
        memory_limit: str = "2G",
        cpu_limit: str = "2",
    ) -> "DeploymentConfig":
        if not _SAFE_NAME.fullmatch(name) or not image:
            raise ValueError("Invalid service configuration")
        if any(not isinstance(value, str) for value in (ports or [])):
            raise ValueError("Ports must be strings")
        self.services.append(
            {
                "name": name,
                "image": image,
                "ports": ports or [],
                "volumes": volumes or [],
                "depends_on": depends_on or [],
                "environment": env or {},
                "healthcheck": healthcheck,
                "memory_limit": memory_limit,
                "cpu_limit": cpu_limit,
            }
        )
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project": self.project_name,
            "services_count": len(self.services),
            "services": [service["name"] for service in self.services],
            "volumes": self.volumes,
            "networks": self.networks,
        }


class DeploymentStatus:
    __slots__ = (
        "containers", "overall_healthy", "total_services", "running",
        "stopped", "deployment_time", "version",
    )

    def __init__(self) -> None:
        self.containers: Dict[str, ContainerHealth] = {}
        self.overall_healthy = False
        self.total_services = 0
        self.running = 0
        self.stopped = 0
        self.deployment_time = 0.0
        self.version = "6.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": "Healthy" if self.overall_healthy else "Unhealthy",
            "version": self.version,
            "total_services": self.total_services,
            "running": self.running,
            "stopped": self.stopped,
            "deployment_time_seconds": round(self.deployment_time, 2),
            "containers": {
                name: health.to_dict()
                for name, health in self.containers.items()
            },
        }


class DockerDeploymentManager:
    """Manage the repository's production Docker deployment."""

    _instance: Optional["DockerDeploymentManager"] = None
    _lock = threading.Lock()
    EXPECTED_SERVICES = ("aios-main", "aios-postgres", "aios-redis")

    def __new__(cls) -> "DockerDeploymentManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._status = DeploymentStatus()
        self._config = DeploymentConfig()
        self._deploy_history: List[Dict[str, Any]] = []
        self._setup_default_config()

    def _setup_default_config(self) -> None:
        self._config.add_service(
            "postgres",
            "postgres:16-alpine",
            healthcheck="pg_isready -U aios -d aios",
            memory_limit="1G",
            cpu_limit="1",
        )
        self._config.add_service(
            "redis",
            "redis:7-alpine",
            healthcheck="redis-cli ping",
            memory_limit="512M",
            cpu_limit="0.5",
        )
        self._config.add_service(
            "aios",
            "aios:latest",
            depends_on=["postgres", "redis"],
            healthcheck="curl -f http://localhost:8000/health",
            memory_limit="2G",
            cpu_limit="2",
        )

    @staticmethod
    def _safe_name(name: str) -> str:
        if not _SAFE_NAME.fullmatch(name):
            raise ValueError("Invalid Docker resource name")
        return name

    @staticmethod
    def _safe_path(value: str) -> str:
        if not value or "\x00" in value:
            raise ValueError("Invalid path")
        return str(Path(value))

    def _run_command(
        self, args: Sequence[str], timeout: int = 10
    ) -> tuple[int, str, str]:
        try:
            result = subprocess.run(
                list(args),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return -1, "", "timeout"
        except OSError as exc:
            return -1, "", str(exc)

    def check_docker_available(self) -> Dict[str, Any]:
        code, output, _ = self._run_command(["docker", "--version"])
        compose_code, compose_output, _ = self._run_command(
            ["docker", "compose", "version"]
        )
        compose_available = compose_code == 0
        if not compose_available:
            legacy_code, legacy_output, _ = self._run_command(
                ["docker-compose", "--version"]
            )
            compose_available = legacy_code == 0
            compose_output = legacy_output if compose_available else ""
        return {
            "docker_available": code == 0,
            "docker_version": output if code == 0 else None,
            "compose_available": compose_available,
            "compose_version": compose_output if compose_available else None,
        }

    def get_container_health(self, name: str) -> ContainerHealth:
        name = self._safe_name(name)
        health = ContainerHealth(name)
        code, output, _ = self._run_command(
            ["docker", "inspect", "--format={{json .State}}", name]
        )
        if code == 0 and output:
            try:
                state = json.loads(output)
                health.status = state.get("Status", "unknown")
                health.healthy = state.get("Health", {}).get("Status") == "healthy"
                health.restarts = int(state.get("RestartCount", 0))
                started = state.get("StartedAt")
                if started and health.status == "running":
                    started_at = datetime.fromisoformat(
                        started.replace("Z", "+00:00")
                    )
                    health.uptime = max(
                        0.0, (datetime.now(timezone.utc) - started_at).total_seconds()
                    )
            except (TypeError, ValueError, json.JSONDecodeError):
                pass

        stats_code, stats_output, _ = self._run_command(
            [
                "docker",
                "stats",
                name,
                "--no-stream",
                "--format={{.MemUsage}} {{.CPUPerc}}",
            ]
        )
        if stats_code == 0 and stats_output:
            parts = stats_output.split()
            memory = parts[0] if parts else "0"
            try:
                number = float(re.sub(r"[^0-9.]", "", memory) or 0)
                if "GiB" in memory or "GB" in memory:
                    number *= 1024
                health.memory_mb = number
                if len(parts) > 1:
                    health.cpu_percent = float(parts[1].replace("%", ""))
            except ValueError:
                pass
        health.last_check = time.time()
        return health

    def check_all_containers(self) -> DeploymentStatus:
        status = DeploymentStatus()
        status.total_services = len(self.EXPECTED_SERVICES)
        for name in self.EXPECTED_SERVICES:
            health = self.get_container_health(name)
            status.containers[name] = health
            if health.status == "running":
                status.running += 1
            else:
                status.stopped += 1
        status.overall_healthy = (
            status.running == status.total_services
            and all(health.healthy for health in status.containers.values())
        )
        self._status = status
        return status

    def deploy(
        self,
        env_file: str = ".env",
        compose_file: str = "docker-compose.yml",
    ) -> Dict[str, Any]:
        env_file = self._safe_path(env_file)
        compose_file = self._safe_path(compose_file)
        started = time.monotonic()
        args = [
            "docker",
            "compose",
            "-f",
            compose_file,
            "--env-file",
            env_file,
            "-p",
            self._config.project_name,
            "up",
            "-d",
            "--build",
        ]
        code, output, error = self._run_command(args, timeout=900)
        record = {
            "timestamp": time.time(),
            "action": "deploy",
            "env_file": env_file,
            "compose_file": compose_file,
            "success": code == 0,
            "output": output[-4000:],
            "error": error[-4000:] if code else None,
            "duration_seconds": round(time.monotonic() - started, 2),
        }
        self._deploy_history.append(record)
        self._deploy_history = self._deploy_history[-20:]
        self._status.deployment_time = time.monotonic() - started
        return record

    def stop(self) -> Dict[str, Any]:
        code, output, error = self._run_command(
            [
                "docker",
                "compose",
                "-f",
                self._config.compose_file,
                "-p",
                self._config.project_name,
                "down",
            ],
            timeout=120,
        )
        return {
            "success": code == 0,
            "output": output,
            "error": error if code else None,
        }

    def restart(self, service: Optional[str] = None) -> Dict[str, Any]:
        args = [
            "docker",
            "compose",
            "-f",
            self._config.compose_file,
            "-p",
            self._config.project_name,
            "restart",
        ]
        if service:
            args.append(self._safe_name(service))
        code, output, error = self._run_command(args, timeout=120)
        return {
            "success": code == 0,
            "output": output,
            "error": error if code else None,
        }

    def get_logs(self, service: str = "aios", lines: int = 50) -> str:
        if not 1 <= lines <= 10000:
            raise ValueError("lines must be 1..10000")
        service = self._safe_name(service)
        _, output, _ = self._run_command(
            [
                "docker",
                "compose",
                "-f",
                self._config.compose_file,
                "-p",
                self._config.project_name,
                "logs",
                f"--tail={lines}",
                service,
            ]
        )
        return output

    def get_deployment_status(self) -> Dict[str, Any]:
        status = self.check_all_containers()
        return {
            "docker": self.check_docker_available(),
            "deployment": status.to_dict(),
            "config": self._config.to_dict(),
            "deploy_history": self._deploy_history[-5:],
            "expected_services": list(self.EXPECTED_SERVICES),
        }

    def verify_deployment(self) -> Dict[str, Any]:
        docker = self.check_docker_available()
        status = self.check_all_containers()
        checks: List[Dict[str, Any]] = [
            {
                "name": "Docker",
                "passed": docker["docker_available"],
                "detail": docker.get("docker_version", "Not found"),
            },
            {
                "name": "Compose",
                "passed": docker["compose_available"],
                "detail": docker.get("compose_version", "Not found"),
            },
        ]
        for name, health in status.containers.items():
            checks.append(
                {
                    "name": name,
                    "passed": health.status == "running" and health.healthy,
                    "running": health.status == "running",
                    "healthy": health.healthy,
                    "restarts": health.restarts,
                }
            )
        return {
            "docker_available": docker["docker_available"],
            "compose_available": docker["compose_available"],
            "containers_running": status.running,
            "containers_expected": status.total_services,
            "services_healthy": sum(
                health.healthy for health in status.containers.values()
            ),
            "checks": checks,
            "overall": (
                docker["docker_available"]
                and docker["compose_available"]
                and status.overall_healthy
            ),
        }


def get_docker_manager() -> DockerDeploymentManager:
    return DockerDeploymentManager()
