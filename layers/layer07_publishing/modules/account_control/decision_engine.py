"""Central UCOS account/platform/niche/content decision engine."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .account_registry import AccountRegistry, AccountSpec
from .policy_registry import PolicyRegistry

@dataclass(frozen=True)
class Decision:
    account_id: str
    platform: str
    niche: str
    topic: str
    content_type: str="post"
    product: Optional[Dict[str,Any]]=None
    affiliate: Optional[Dict[str,Any]]=None
    policy_version: Optional[str]=None
    reasons: List[str]=field(default_factory=list)

class DecisionEngine:
    def __init__(self,registry:Optional[AccountRegistry]=None,policies:Optional[PolicyRegistry]=None)->None:
        self.registry=registry or AccountRegistry(); self.policies=policies or PolicyRegistry()
    @staticmethod
    def _score(account:AccountSpec,topic:str)->int:
        return int(hashlib.sha256(f"{account.account_id}|{topic}".encode()).hexdigest()[:12],16)
    def choose_account(self,topic:str,platform:Optional[str]=None)->AccountSpec:
        accounts=self.registry.list(platform=platform,enabled_only=True)
        if not accounts: raise LookupError(f"no enabled account configured for platform={platform or '*'}")
        return max(accounts,key=lambda account:self._score(account,topic))
    def choose_content_type(self,account:AccountSpec,topic:str)->str:
        allowed=set(account.capabilities or ["post"]); policy=self.policies.get(account.platform); policy_types=set((policy.constraints.get("content_types") if policy else None) or allowed)
        intersection=allowed & policy_types
        if not intersection: raise ValueError(f"account {account.account_id} has no content type permitted by {account.platform} policy")
        for value in ("video","photo","post"):
            if value in intersection: return value
        return sorted(intersection)[0]
    def decide(self,topic:str,platform:Optional[str]=None,product:Optional[Dict[str,Any]]=None,affiliate:Optional[Dict[str,Any]]=None)->Decision:
        if not topic.strip(): raise ValueError("topic is required")
        account=self.choose_account(topic,platform); policy=self.policies.get(account.platform)
        return Decision(account_id=account.account_id,platform=account.platform,niche=account.niche,topic=topic.strip(),content_type=self.choose_content_type(account,topic),product=product,affiliate=affiliate,policy_version=policy.version if policy else None,reasons=["enabled account","platform/niche match","capability/policy intersection"])
