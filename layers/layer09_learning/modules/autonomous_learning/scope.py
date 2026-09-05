"""Strongly typed learning scope identity.

Every persisted observation/model is keyed by the complete scope. Empty values
are normalized to explicit ``*`` only for dimensions where global scope is
intentionally requested by the caller.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib


@dataclass(frozen=True)
class LearningScope:
    platform_id: str
    niche_id: str
    audience_id: str = "*"
    country: str = "*"
    language: str = "*"
    content_type: str = "*"

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            if not value or not value.strip():
                raise ValueError(f"{name} cannot be empty")

    @property
    def key(self) -> str:
        raw = "|".join((self.platform_id, self.niche_id, self.audience_id, self.country, self.language, self.content_type))
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
        return f"{self.platform_id}:{self.niche_id}:{digest}"

    @property
    def dimensions(self) -> dict[str, str]:
        return {
            "platform_id": self.platform_id,
            "niche_id": self.niche_id,
            "audience_id": self.audience_id,
            "country": self.country,
            "language": self.language,
            "content_type": self.content_type,
        }
