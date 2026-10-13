"""Capability-based agent registry; publisher selection is platform-based, not account-based."""
from __future__ import annotations

from typing import Iterable

from .contracts import AgentManifest, AgentRole, AgentTask


class AgentRegistryError(RuntimeError):
    pass


class AgentRegistry:
    def __init__(self) -> None:
        self._manifests: dict[AgentRole, AgentManifest] = {}

    def register(self, manifest: AgentManifest) -> None:
        existing = self._manifests.get(manifest.role)
        if existing and existing != manifest:
            raise AgentRegistryError("agent role already registered with a different manifest")
        for current in self._manifests.values():
            if manifest.role.name.startswith("PUBLISH_") and current.role != manifest.role:
                if current.platform and manifest.platform and current.platform.casefold() == manifest.platform.casefold():
                    raise AgentRegistryError("a publisher agent is already registered for platform " + manifest.platform)
        self._manifests[manifest.role] = manifest

    def get(self, role: AgentRole) -> AgentManifest:
        manifest = self._manifests.get(role)
        if manifest is None or not manifest.enabled:
            raise AgentRegistryError("agent is not registered or is disabled: " + role.value)
        return manifest

    def find_capability(self, capability: str) -> tuple[AgentManifest, ...]:
        if not capability.strip():
            raise ValueError("capability is required")
        matches = [
            manifest for manifest in self._manifests.values()
            if manifest.enabled and capability in manifest.capabilities
        ]
        return tuple(sorted(matches, key=lambda item: (item.role.value, item.version)))

    def publisher_for(self, platform: str, task: AgentTask) -> AgentManifest:
        if not platform.strip():
            raise ValueError("platform is required")
        if not task.scope.platform_account_ref:
            raise AgentRegistryError("publishing requires an explicitly selected platform account")
        expected = "publish:" + platform.casefold()
        matches = [
            manifest for manifest in self._manifests.values()
            if manifest.enabled
            and manifest.role.name.startswith("PUBLISH_")
            and manifest.platform
            and manifest.platform.casefold() == platform.casefold()
            and expected in manifest.capabilities
        ]
        if len(matches) != 1:
            raise AgentRegistryError(
                "expected exactly one enabled publisher for platform " + platform
            )
        return matches[0]

    def list_enabled(self) -> tuple[AgentManifest, ...]:
        return tuple(m for m in self._manifests.values() if m.enabled)
