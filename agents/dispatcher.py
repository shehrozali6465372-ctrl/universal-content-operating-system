"""Deterministic dispatcher for the UCOS worker-agent roster.

Only agents with an implemented entry point can be dispatched. Production mode is
blocked until that agent's manifest status is explicitly production_ready.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping


class AgentDispatchError(RuntimeError):
    """Base error for rejected agent dispatches."""


class AgentNotImplementedError(AgentDispatchError):
    """The requested worker has not been implemented yet."""


class AgentNotProductionReadyError(AgentDispatchError):
    """The worker is implemented but is not production-certified."""


class AgentDispatcher:
    """Dispatch typed JSON-like payloads to named worker agents."""

    def __init__(
        self,
        *,
        manifest_path: str | Path | None = None,
        factories: Mapping[str, Callable[..., Any]] | None = None,
    ) -> None:
        self.manifest_path = Path(manifest_path) if manifest_path else Path(__file__).with_name("manifest.json")
        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AgentDispatchError("agent manifest is missing or invalid") from exc
        agents = manifest.get("agents")
        if not isinstance(agents, list):
            raise AgentDispatchError("agent manifest must contain an agents list")
        self._agents: dict[str, dict[str, Any]] = {}
        for spec in agents:
            if not isinstance(spec, dict) or not str(spec.get("id") or "").strip():
                raise AgentDispatchError("every manifest worker must have an id")
            agent_id = str(spec["id"]).strip().upper()
            if agent_id in self._agents:
                raise AgentDispatchError(f"duplicate worker id: {agent_id}")
            self._agents[agent_id] = spec
        self._factories = dict(factories or {})

    def list_agents(self) -> list[dict[str, Any]]:
        """Return compact worker metadata without exposing runtime secrets."""
        return [
            {
                "id": agent_id,
                "name": spec.get("name", ""),
                "status": spec.get("status", "unknown"),
                "entrypoint": spec.get("entrypoint", ""),
            }
            for agent_id, spec in self._agents.items()
        ]

    def dispatch(
        self,
        agent_id: str,
        *,
        constructor_kwargs: Mapping[str, Any],
        input_payload: Mapping[str, Any],
        mode: str = "staging",
    ) -> dict[str, Any]:
        """Run one implemented agent and return its JSON-compatible report."""
        key = str(agent_id or "").strip().upper()
        selected_mode = str(mode or "").strip().lower()
        if selected_mode not in {"test", "staging", "production"}:
            raise ValueError("mode must be test, staging, or production")
        spec = self._agents.get(key)
        if spec is None:
            raise AgentNotImplementedError("worker id is not present in the manifest")
        status = str(spec.get("status") or "planned").lower()
        if status == "planned":
            raise AgentNotImplementedError(f"{key} is planned but has no released implementation")
        if selected_mode == "production" and status != "production_ready":
            raise AgentNotProductionReadyError(
                f"{key} status is {status}; production dispatch requires production_ready"
            )

        factory = self._factories.get(key)
        if factory is None and key == "AG01":
            from agents.agent_01_research_discovery import ResearchDiscoveryAgent

            factory = ResearchDiscoveryAgent
        if factory is None:
            raise AgentNotImplementedError(f"{key} has no registered implementation")

        instance = factory(**dict(constructor_kwargs))
        run = getattr(instance, "run", None)
        if not callable(run):
            raise AgentDispatchError(f"{key} implementation does not expose run()")
        result = run(**dict(input_payload))
        if not isinstance(result, dict):
            raise AgentDispatchError(f"{key} must return a dictionary report")
        # Do not let an agent return a different account identity than it was
        # constructed for and then have that report mistaken for the requested job.
        requested_account = str(dict(constructor_kwargs).get("account_id") or "").strip()
        reported_account = str(result.get("account_id") or "").strip()
        if requested_account and reported_account and requested_account != reported_account:
            raise AgentDispatchError("agent report account_id does not match the requested account")
        return result
