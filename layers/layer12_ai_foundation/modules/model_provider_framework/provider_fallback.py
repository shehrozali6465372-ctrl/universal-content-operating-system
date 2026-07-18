"""provider_fallback.py — Fallback logic between providers."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class FallbackChain:
    """A chain of providers to try in order."""
    __slots__ = ("name", "chain", "current_index", "status")

    def __init__(self, name: str, chain: List[str]) -> None:
        self.name = name
        self.chain = chain
        self.current_index = 0
        self.status = "active"

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "chain": self.chain,
                "current_index": self.current_index, "status": self.status}


class ProviderFallback:
    """Manages fallback chains between providers."""

    def __init__(self) -> None:
        self._chains: Dict[str, FallbackChain] = {}
        self._failures: Dict[str, int] = {}

    def add_chain(self, name: str, providers: List[str]) -> FallbackChain:
        chain = FallbackChain(name, providers)
        self._chains[name] = chain
        return chain

    def get_next_provider(self, chain_name: str) -> Optional[str]:
        chain = self._chains.get(chain_name)
        if not chain or chain.current_index >= len(chain.chain):
            return None
        return chain.chain[chain.current_index]

    def advance(self, chain_name: str) -> Optional[str]:
        chain = self._chains.get(chain_name)
        if not chain:
            return None
        chain.current_index += 1
        return self.get_next_provider(chain_name)

    def reset(self, chain_name: str) -> None:
        chain = self._chains.get(chain_name)
        if chain:
            chain.current_index = 0

    def record_failure(self, provider: str) -> int:
        self._failures[provider] = self._failures.get(provider, 0) + 1
        return self._failures[provider]

    def get_failures(self, provider: str) -> int:
        return self._failures.get(provider, 0)

    def get_chain(self, name: str) -> Optional[FallbackChain]:
        return self._chains.get(name)

    def to_dict(self) -> Dict[str, Any]:
        return {"chains": {k: v.to_dict() for k, v in self._chains.items()},
                "failures": dict(self._failures)}
