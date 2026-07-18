"""user_repository.py — User repository."""
from __future__ import annotations
from typing import Any, Dict, Optional
from layers.layer13_persistence.modules.repository_layer.base_repository import BaseRepository, BaseEntity


class UserEntity(BaseEntity):
    __slots__ = ("username", "email", "role", "platforms")

    def __init__(self, username: str, email: str, role: str = "user") -> None:
        super().__init__()
        self.username = username
        self.email = email
        self.role = role
        self.platforms: list = []

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({"username": self.username, "email": self.email, "role": self.role})
        return base


class UserRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("user")

    def find_by_email(self, email: str) -> Optional[UserEntity]:
        return self.find_one(email=email)

    def find_by_username(self, username: str) -> Optional[UserEntity]:
        return self.find_one(username=username)

    def find_by_role(self, role: str):
        return self.find(role=role)
