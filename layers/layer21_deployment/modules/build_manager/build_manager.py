"""BuildManager — build pipeline management."""
from __future__ import annotations
import time
import uuid
from typing import Any, Dict, List, Optional
from enum import Enum


class BuildStatus(str, Enum):
    QUEUED = "queued"; RUNNING = "running"; SUCCESS = "success"; FAILED = "failed"


class BuildStep:
    __slots__ = ("name", "command", "status", "duration_ms", "output")

    def __init__(self, name: str, command: str) -> None:
        self.name = name
        self.command = command
        self.status = BuildStatus.QUEUED
        self.duration_ms: float = 0.0
        self.output = ""


class Build:
    __slots__ = ("build_id", "version", "steps", "status", "started_at",
                 "finished_at", "metadata")

    def __init__(self, version: str) -> None:
        self.build_id = str(uuid.uuid4())[:12]
        self.version = version
        self.steps: List[BuildStep] = []
        self.status = BuildStatus.QUEUED
        self.started_at: float = 0.0
        self.finished_at: float = 0.0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"build_id": self.build_id, "version": self.version,
                "status": self.status.value, "steps": len(self.steps)}


class BuildManager:
    def __init__(self) -> None:
        self._builds: Dict[str, Build] = {}
        self._default_steps = ["lint", "test", "build", "package"]

    def create_build(self, version: str, steps: Optional[List[str]] = None) -> Build:
        build = Build(version)
        for step_name in (steps or self._default_steps):
            build.steps.append(BuildStep(step_name, f"run_{step_name}"))
        self._builds[build.build_id] = build
        return build

    def execute_build(self, build_id: str) -> Dict[str, Any]:
        build = self._builds.get(build_id)
        if not build:
            return {"error": "build_not_found"}
        build.status = BuildStatus.RUNNING
        build.started_at = time.time()
        for step in build.steps:
            step.status = BuildStatus.RUNNING
            step.duration_ms = 100.0
            step.status = BuildStatus.SUCCESS
        build.status = BuildStatus.SUCCESS
        build.finished_at = time.time()
        return build.to_dict()

    def get_build(self, build_id: str) -> Optional[Build]:
        return self._builds.get(build_id)

    def list_builds(self) -> List[Dict[str, Any]]:
        return [b.to_dict() for b in self._builds.values()]
