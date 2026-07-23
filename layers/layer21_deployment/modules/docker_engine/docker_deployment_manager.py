"""DockerDeploymentManager — Production Docker deployment, health, and orchestration."""
from __future__ import annotations
import json
import os
import subprocess
import shlex
import threading
import time
from typing import Any, Dict, List, Optional


class ContainerHealth:
    __slots__ = ("name", "status", "healthy", "uptime", "restarts", "memory_mb", "cpu_percent", "last_check")

    def __init__(self, name: str) -> None:
        self.name = name
        self.status = "unknown"
        self.healthy = False
        self.uptime = 0
        self.restarts = 0
        self.memory_mb = 0.0
        self.cpu_percent = 0.0
        self.last_check = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "healthy": self.healthy,
            "uptime_seconds": self.uptime,
            "restarts": self.restarts,
            "memory_mb": round(self.memory_mb, 1),
            "cpu_percent": round(self.cpu_percent, 1),
        }


class DeploymentConfig:
    __slots__ = ("project_name", "services", "volumes", "networks", "env_file", "compose_file")

    def __init__(self, project_name: str = "aios") -> None:
        self.project_name = project_name
        self.services: List[Dict[str, Any]] = []
        self.volumes: List[str] = []
        self.networks: List[str] = ["aios-net"]
        self.env_file = ".env"
        self.compose_file = "docker-compose.yml"

    def add_service(self, name: str, image: str, ports: List[str] = None,
                    volumes: List[str] = None, depends_on: List[str] = None,
                    env: Dict[str, str] = None, healthcheck: str = None,
                    memory_limit: str = "2G", cpu_limit: str = "2") -> "DeploymentConfig":
        svc: Dict[str, Any] = {
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
        self.services.append(svc)
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project": self.project_name,
            "services_count": len(self.services),
            "services": [s["name"] for s in self.services],
            "volumes": self.volumes,
            "networks": self.networks,
        }


class DeploymentStatus:
    __slots__ = ("containers", "overall_healthy", "total_services", "running",
                 "stopped", "deployment_time", "version")

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
            "containers": {k: v.to_dict() for k, v in self.containers.items()},
        }


class DockerDeploymentManager:
    """Manages Docker-based production deployment with health monitoring."""
    _instance: Optional["DockerDeploymentManager"] = None
    _lock = threading.Lock()

    EXPECTED_SERVICES = ["aios", "aios-worker", "postgres", "redis"]

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
            "postgres", "postgres:16-alpine",
            ports=["5432:5432"],
            env={"POSTGRES_DB": "aios", "POSTGRES_USER": "aios"},
            healthcheck="pg_isready -U aios",
            memory_limit="1G", cpu_limit="1",
        )
        self._config.add_service(
            "redis", "redis:7-alpine",
            ports=["6379:6379"],
            healthcheck="redis-cli ping",
            memory_limit="512M", cpu_limit="0.5",
        )
        self._config.add_service(
            "aios", "aios:latest",
            ports=["8000:8000"],
            depends_on=["postgres", "redis"],
            memory_limit="2G", cpu_limit="2",
        )
        self._config.add_service(
            "aios-worker", "aios:latest",
            depends_on=["postgres", "redis"],
            memory_limit="1G", cpu_limit="1",
        )

    def _run_command(self, cmd: str, timeout: int = 10) -> tuple:
        try:
            args = shlex.split(cmd)
            result = subprocess.run(
                args, capture_output=True, text=True, timeout=timeout
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return -1, "", "timeout"
        except Exception as e:
            return -1, "", str(e)

    def check_docker_available(self) -> Dict[str, Any]:
        code, out, err = self._run_command("docker --version")
        compose_available = False
        code2, out2, _ = self._run_command("docker compose version")
        if code2 == 0:
            compose_available = True
        else:
            code3, out3, _ = self._run_command("docker-compose --version")
            if code3 == 0:
                compose_available = True

        return {
            "docker_available": code == 0,
            "docker_version": out if code == 0 else None,
            "compose_available": compose_available,
            "compose_version": out2 if compose_available else None,
        }

    def get_container_health(self, name: str) -> ContainerHealth:
        health = ContainerHealth(name)
        code, out, _ = self._run_command(
            f"docker inspect --format='{{{{.State.Status}}}} {{{{.State.Health.Status}}}} "
            f"{{{{.RestartCount}}}} {{{{.State.StartedAt}}}}' {name} 2>/dev/null"
        )
        if code == 0 and out:
            parts = out.split()
            if len(parts) >= 2:
                health.status = parts[0]
                health.healthy = parts[1] == "healthy"
            if len(parts) >= 3:
                try:
                    health.restarts = int(parts[2])
                except ValueError:
                    pass

        # Memory and CPU
        code2, out2, _ = self._run_command(
            f"docker stats {name} --no-stream --format='{{{{.MemUsage}}}} {{{{.CPUPerc}}}}' 2>/dev/null"
        )
        if code2 == 0 and out2:
            mem_str = out2.split()[0] if out2.split() else "0MB"
            cpu_str = out2.split()[1] if len(out2.split()) > 1 else "0%"
            try:
                if "MB" in mem_str:
                    health.memory_mb = float(mem_str.replace("MB", ""))
                elif "GB" in mem_str:
                    health.memory_mb = float(mem_str.replace("GB", "")) * 1024
                health.cpu_percent = float(cpu_str.replace("%", ""))
            except (ValueError, IndexError):
                pass

        health.last_check = time.time()
        return health

    def check_all_containers(self) -> DeploymentStatus:
        status = DeploymentStatus()
        status.total_services = len(self.EXPECTED_SERVICES)

        for name in self.EXPECTED_SERVICES:
            health = self.get_container_health(name)
            status.containers[name] = health
            if health.status in ("running",):
                status.running += 1
            else:
                status.stopped += 1

        status.overall_healthy = status.running == status.total_services
        self._status = status
        return status

    def deploy(self, env_file: str = ".env") -> Dict[str, Any]:
        start = time.time()
        deploy_record = {
            "timestamp": time.time(),
            "action": "deploy",
            "env_file": env_file,
            "success": False,
        }

        code, out, err = self._run_command(
            f"docker compose --env-file {env_file} up -d --build", timeout=300
        )

        deploy_record["success"] = code == 0
        deploy_record["output"] = out
        deploy_record["error"] = err if code != 0 else None
        deploy_record["duration_seconds"] = round(time.time() - start, 2)

        self._deploy_history.append(deploy_record)
        self._status.deployment_time = time.time() - start

        return deploy_record

    def stop(self) -> Dict[str, Any]:
        code, out, err = self._run_command("docker compose down", timeout=60)
        return {"success": code == 0, "output": out, "error": err}

    def restart(self, service: Optional[str] = None) -> Dict[str, Any]:
        cmd = "docker compose restart"
        if service:
            cmd += f" {service}"
        code, out, err = self._run_command(cmd, timeout=120)
        return {"success": code == 0, "output": out, "error": err}

    def get_logs(self, service: str = "aios", lines: int = 50) -> str:
        _, out, _ = self._run_command(f"docker compose logs --tail={lines} {service}")
        return out

    def get_deployment_status(self) -> Dict[str, Any]:
        status = self.check_all_containers()
        docker_info = self.check_docker_available()

        return {
            "docker": docker_info,
            "deployment": status.to_dict(),
            "config": self._config.to_dict(),
            "deploy_history": self._deploy_history[-5:],
            "expected_services": self.EXPECTED_SERVICES,
        }

    def verify_deployment(self) -> Dict[str, Any]:
        """Full deployment verification: Docker, containers, connectivity."""
        results: Dict[str, Any] = {
            "docker_available": False,
            "compose_available": False,
            "containers_running": 0,
            "containers_expected": len(self.EXPECTED_SERVICES),
            "services_healthy": 0,
            "checks": [],
            "overall": False,
        }

        # Check Docker
        docker = self.check_docker_available()
        results["docker_available"] = docker["docker_available"]
        results["compose_available"] = docker["compose_available"]
        results["checks"].append({
            "name": "Docker",
            "passed": docker["docker_available"],
            "detail": docker.get("docker_version", "Not found"),
        })

        # Check containers
        status = self.check_all_containers()
        for name, health in status.containers.items():
            results["checks"].append({
                "name": name,
                "passed": health.status == "running",
                "healthy": health.healthy,
                "detail": health.status,
            })
            if health.status == "running":
                results["containers_running"] += 1
            if health.healthy:
                results["services_healthy"] += 1

        results["overall"] = (
            results["docker_available"]
            and results["containers_running"] == results["containers_expected"]
        )
        return results


def get_docker_manager() -> DockerDeploymentManager:
    return DockerDeploymentManager()
