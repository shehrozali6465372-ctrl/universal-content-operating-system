"""DockerEngine — Docker configuration and container management."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class DockerConfig:
    __slots__ = ("image", "tag", "ports", "volumes", "env_vars", "memory_limit",
                 "cpu_limit", "restart_policy", "metadata")

    def __init__(self, image: str = "aios", tag: str = "latest") -> None:
        self.image = image
        self.tag = tag
        self.ports: List[str] = []
        self.volumes: List[str] = []
        self.env_vars: Dict[str, str] = {}
        self.memory_limit = "2g"
        self.cpu_limit = "2"
        self.restart_policy = "unless-stopped"
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"image": f"{self.image}:{self.tag}", "ports": self.ports,
                "volumes": self.volumes, "memory": self.memory_limit}

    def generate_dockerfile(self) -> str:
        return f"""FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "main.py"]"""


class DockerCompose:
    def __init__(self, project_name: str = "aios") -> None:
        self.project_name = project_name
        self.services: Dict[str, DockerConfig] = {}

    def add_service(self, name: str, config: DockerConfig) -> None:
        self.services[name] = config

    def generate(self) -> str:
        lines = [f"version: '3.8'", f"services:"]
        for name, config in self.services.items():
            lines.append(f"  {name}:")
            lines.append(f"    image: {config.image}:{config.tag}")
            if config.ports:
                lines.append(f"    ports:")
                for port in config.ports:
                    lines.append(f"      - {port}")
            lines.append(f"    restart: {config.restart_policy}")
        return "\n".join(lines)


class DockerEngine:
    def __init__(self) -> None:
        self._configs: Dict[str, DockerConfig] = {}
        self._compose = DockerCompose()

    def create_config(self, name: str, image: str = "aios", tag: str = "latest") -> DockerConfig:
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
        return list(self._configs.keys())
