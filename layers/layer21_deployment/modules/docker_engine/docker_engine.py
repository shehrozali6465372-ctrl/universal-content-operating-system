"""Safe Docker and Compose configuration generation."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

_SAFE = re.compile(r"^[A-Za-z0-9_.-]+$")


class DockerConfig:
    __slots__ = (
        "image", "tag", "ports", "volumes", "env_vars",
        "memory_limit", "cpu_limit", "restart_policy",
        "metadata", "command", "healthcheck",
    )

    def __init__(self, image: str = "aios", tag: str = "stable") -> None:
        if not image or not tag or not _SAFE.fullmatch(tag):
            raise ValueError("Invalid Docker image/tag")
        self.image = image
        self.tag = tag
        self.ports: List[str] = []
        self.volumes: List[str] = []
        self.env_vars: Dict[str, str] = {}
        self.memory_limit = "2g"
        self.cpu_limit = "2"
        self.restart_policy = "unless-stopped"
        self.metadata: Dict[str, Any] = {}
        self.command: Optional[str] = None
        self.healthcheck: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "image": f"{self.image}:{self.tag}",
            "ports": list(self.ports),
            "volumes": list(self.volumes),
            "memory": self.memory_limit,
            "cpu": self.cpu_limit,
            "restart": self.restart_policy,
            "healthcheck": self.healthcheck,
        }

    def generate_dockerfile(self) -> str:
        return "\n".join(
            [
                f"FROM {self.image}:{self.tag}",
                "WORKDIR /app",
                "COPY . .",
                "EXPOSE 8000",
                'CMD ["python", "main.py", "--api"]',
            ]
        )


class DockerCompose:
    def __init__(self, project_name: str = "aios") -> None:
        if not _SAFE.fullmatch(project_name):
            raise ValueError("Invalid project name")
        self.project_name = project_name
        self.services: Dict[str, DockerConfig] = {}

    def add_service(self, name: str, config: DockerConfig) -> None:
        if not _SAFE.fullmatch(name):
            raise ValueError("Invalid service name")
        self.services[name] = config

    def generate(self) -> str:
        lines = ["services:"]
        for name, config in self.services.items():
            lines.extend(
                [
                    f"  {name}:",
                    f"    image: {config.image}:{config.tag}",
                    f"    restart: {config.restart_policy}",
                ]
            )
            if config.ports:
                lines.append("    ports:")
                lines.extend(f"      - {port}" for port in config.ports)
            if config.volumes:
                lines.append("    volumes:")
                lines.extend(f"      - {volume}" for volume in config.volumes)
            if config.env_vars:
                lines.append("    environment:")
                lines.extend(
                    f"      {key}: {value}"
                    for key, value in config.env_vars.items()
                )
            if config.healthcheck:
                lines.extend(
                    ["    healthcheck:", f"      test: {config.healthcheck}"]
                )
        return "\n".join(lines) + "\n"


class DockerEngine:
    def __init__(self) -> None:
        self._configs: Dict[str, DockerConfig] = {}
        self._compose = DockerCompose()

    def create_config(
        self, name: str, image: str = "aios", tag: str = "stable"
    ) -> DockerConfig:
        if not _SAFE.fullmatch(name):
            raise ValueError("Invalid config name")
        config = DockerConfig(image, tag)
        self._configs[name] = config
        self._compose.add_service(name, config)
        return config

    def get_config(self, name: str) -> Optional[DockerConfig]:
        return self._configs.get(name)

    def generate_compose(self) -> str:
        return self._compose.generate()

    def generate_dockerfile(self, config_name: str) -> str:
        config = self._configs.get(config_name)
        return config.generate_dockerfile() if config else ""

    def list_configs(self) -> List[str]:
        return list(self._configs)
