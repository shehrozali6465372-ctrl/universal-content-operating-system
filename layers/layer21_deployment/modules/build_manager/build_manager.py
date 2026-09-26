"""Production build orchestration with real command execution and fail-closed results."""
from __future__ import annotations
import shlex
import subprocess
import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence

class BuildStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

class BuildStep:
    __slots__ = ("name", "command", "status", "duration_ms", "output")
    def __init__(self, name: str, command: str) -> None:
        if not name or not command:
            raise ValueError("Build step name and command are required")
        self.name, self.command = name, command
        self.status = BuildStatus.QUEUED
        self.duration_ms = 0.0
        self.output = ""
    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "command": self.command, "status": self.status.value,
                "duration_ms": round(self.duration_ms, 2), "output": self.output}

class Build:
    __slots__ = ("build_id", "version", "steps", "status", "started_at", "finished_at", "metadata")
    def __init__(self, version: str) -> None:
        self.build_id = str(uuid.uuid4())
        self.version = version
        self.steps: List[BuildStep] = []
        self.status = BuildStatus.QUEUED
        self.started_at = self.finished_at = 0.0
        self.metadata: Dict[str, Any] = {}
    def to_dict(self) -> Dict[str, Any]:
        return {"build_id": self.build_id, "version": self.version, "status": self.status.value,
                "steps": [step.to_dict() for step in self.steps],
                "started_at": self.started_at, "finished_at": self.finished_at}

CommandRunner = Callable[[Sequence[str], int], tuple[int, str, str]]

def _default_runner(args: Sequence[str], timeout: int) -> tuple[int, str, str]:
    try:
        result = subprocess.run(list(args), capture_output=True, text=True,
                                timeout=timeout, check=False)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "command timed out"
    except OSError as exc:
        return -1, "", str(exc)

class BuildManager:
    """Build manager that never reports success without executing every step."""
    def __init__(self, runner: Optional[CommandRunner] = None, timeout: int = 900) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self._builds: Dict[str, Build] = {}
        self._runner = runner or _default_runner
        self._timeout = timeout

    def create_build(self, version: str, steps: Optional[List[str]] = None) -> Build:
        build = Build(version)
        for command in steps or ["python -m compileall -q layers", "python -m pytest -q"]:
            if not shlex.split(command):
                raise ValueError("Build command cannot be empty")
            build.steps.append(BuildStep(command, command))
        self._builds[build.build_id] = build
        return build

    def execute_build(self, build_id: str) -> Dict[str, Any]:
        build = self._builds.get(build_id)
        if build is None:
            return {"error": "build_not_found", "build_id": build_id}
        build.status = BuildStatus.RUNNING
        build.started_at = time.time()
        for step in build.steps:
            step.status = BuildStatus.RUNNING
            started = time.monotonic()
            code, stdout, stderr = self._runner(shlex.split(step.command), self._timeout)
            step.duration_ms = (time.monotonic() - started) * 1000
            step.output = stdout if code == 0 else stderr or stdout
            if code != 0:
                step.status = BuildStatus.FAILED
                build.status = BuildStatus.FAILED
                build.finished_at = time.time()
                return build.to_dict()
            step.status = BuildStatus.SUCCESS
        build.status = BuildStatus.SUCCESS
        build.finished_at = time.time()
        return build.to_dict()

    def get_build(self, build_id: str) -> Optional[Build]:
        return self._builds.get(build_id)
    def list_builds(self) -> List[Dict[str, Any]]:
        return [build.to_dict() for build in self._builds.values()]
