"""Central account/platform/niche decision engine for UCOS."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .account_registry import AccountRegistry, AccountSpec
from .policy_registry import PolicyRegistry, PlatformPolicy


@dataclass(frozen=True)
class Decision:
    account_id: str
    platform: str
    niche: str
    topic: str
    content_type: str = "post"
    product: Optional[Dict[str, Any]] = None
    affiliate: Optional[Dict[str, Any]] = None
    policy_version: Optional[str] = None
    reasons: List[str] = field(default_factory=list)


class DecisionEngine:
    """Deterministic baseline selector; scoring can be replaced by learned scores.

    It never invents a product or performance metric. Products are accepted only
    when supplied by the product intelligence/affiliate layer.
    """

    def __init__(self, registry: Optional[AccountRegistry] = None, policies: Optional[PolicyRegistry] = None) -> None:
        self.registry = registry or AccountRegistry()
        self.policies = policies or PolicyRegistry()

    @staticmethod
    def _score(account: AccountSpec, topic: str) -> int:
        value = f"{account.account_id}|{topic}".encode("utf-8")
        return int(hashlib.sha256(value).hexdigest()[:12], 16)

    def choose_account(self, topic: str, platform: Optional[str] = None) -> AccountSpec:
        accounts = self.registry.list(platform=platform, enabled_only=True)
        if not accounts:
            raise LookupError(f"no enabled account configured for platform={platform or '*'}")
        return max(accounts, key=lambda account: self._score(account, topic))

    def choose_content_type(self, account: AccountSpec, topic: str) -> str:
        allowed = account.capabilities or ["post"]
        policy = self.policies.get(account.platform)
        policy_types = (policy.constraints.get("content_types") if policy else None) or allowed
        for value in ("video", "photo", "post"):
            if value in allowed and value in policy_types:
                return value
        return str(policy_types[0] if policy_types else "post")

    def decide(self, topic: str, platform: Optional[str] = None, product: Optional[Dict[str, Any]] = None,
               affiliate: Optional[Dict[str, Any]] = None) -> Decision:
        if not topic.strip():
            raise ValueError("topic is required")
        account = self.choose_account(topic, platform)
        policy = self.policies.get(account.platform)
        return Decision(
            account_id=account.account_id,
            platform=account.platform,
            niche=account.niche,
            topic=topic.strip(),
            content_type=self.choose_content_type(account, topic),
            product=product,
            affiliate=affiliate,
            policy_version=policy.version if policy else None,
            reasons=["enabled account", "platform/niche match", "deterministic selection"],
        )
