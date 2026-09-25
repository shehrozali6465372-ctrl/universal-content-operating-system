"""Canonical content artifact and platform variants."""
from __future__ import annotations

from dataclasses import dataclass, field
from copy import deepcopy
from typing import Any, Dict, List, Optional


@dataclass
class ContentArtifact:
    artifact_id: str
    account_id: str
    platform: str
    niche: str
    topic: str
    body: str
    content_type: str = "post"
    title: str = ""
    media: List[Dict[str, Any]] = field(default_factory=list)
    product: Optional[Dict[str, Any]] = None
    affiliate: Optional[Dict[str, Any]] = None
    policy_version: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        for name in ("artifact_id", "account_id", "platform", "niche", "topic", "body"):
            if not getattr(self, name, "").strip():
                raise ValueError(f"{name} is required")

    def variant(self, *, platform: Optional[str] = None, body: Optional[str] = None,
                content_type: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.validate()
        return {
            "artifact_id": self.artifact_id,
            "account_id": self.account_id,
            "platform": platform or self.platform,
            "niche": self.niche,
            "topic": self.topic,
            "title": self.title,
            "body": body if body is not None else self.body,
            "content_type": content_type or self.content_type,
            "media": deepcopy(self.media),
            "product": deepcopy(self.product),
            "affiliate": deepcopy(self.affiliate),
            "policy_version": self.policy_version,
            "metadata": {**deepcopy(self.metadata), **deepcopy(metadata or {})},
        }
