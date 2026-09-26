"""Role-based authorization for Layer 17."""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Set
from typing import Any


class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    PUBLISH = "publish"
    ANALYZE = "analyze"
    LEARN = "learn"


class Role:
    __slots__ = ("role_id", "name", "permissions", "description", "metadata")

    def __init__(self, name: str, permissions: Optional[Set[Permission]] = None) -> None:
        if not name:
            raise ValueError("role name is required")
        self.role_id = f"role_{name}"
        self.name = name
        self.permissions = set(permissions or set())
        self.description = ""
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"role_id": self.role_id, "name": self.name,
                "permissions": sorted(p.value for p in self.permissions)}


class AuthorizationManager:
    def __init__(self) -> None:
        self._roles: Dict[str, Role] = {}
        self._user_roles: Dict[str, Set[str]] = {}

    def create_role(self, name: str, permissions: Optional[Set[Permission]] = None) -> Role:
        role = Role(name, permissions)
        if role.role_id in self._roles:
            raise ValueError("role already exists")
        self._roles[role.role_id] = role
        return role

    def assign_role(self, user_id: str, role_id: str) -> bool:
        if not user_id or role_id not in self._roles:
            return False
        self._user_roles.setdefault(user_id, set()).add(role_id)
        return True

    def revoke_role(self, user_id: str, role_id: str) -> bool:
        roles = self._user_roles.get(user_id)
        if not roles or role_id not in roles:
            return False
        roles.remove(role_id)
        if not roles:
            self._user_roles.pop(user_id, None)
        return True

    def has_permission(self, user_id: str, permission: Permission) -> bool:
        return any(
            role is not None and permission in role.permissions
            for role_id in self._user_roles.get(user_id, set())
            for role in [self._roles.get(role_id)]
        )

    def get_user_roles(self, user_id: str) -> List[str]:
        return sorted(self._user_roles.get(user_id, set()))

    def get_role_permissions(self, role_id: str) -> Set[Permission]:
        role = self._roles.get(role_id)
        return set(role.permissions) if role else set()

    def list_roles(self) -> List[Dict[str, Any]]:
        return [role.to_dict() for role in self._roles.values()]

    def stats(self) -> Dict[str, Any]:
        return {"roles": len(self._roles),
                "assignments": sum(len(values) for values in self._user_roles.values())}
