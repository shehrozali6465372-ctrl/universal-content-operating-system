"""Authorization — role-based access control."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional, Set
from enum import Enum


class Permission(str, Enum):
    READ = "read"; WRITE = "write"; DELETE = "delete"; ADMIN = "admin"
    PUBLISH = "publish"; ANALYZE = "analyze"; LEARN = "learn"


class Role:
    __slots__ = ("role_id", "name", "permissions", "description", "metadata")

    def __init__(self, name: str, permissions: Optional[Set[Permission]] = None) -> None:
        self.role_id = f"role_{name}"
        self.name = name
        self.permissions = permissions or set()
        self.description = ""
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"role_id": self.role_id, "name": self.name,
                "permissions": [p.value for p in self.permissions]}


class AuthorizationManager:
    def __init__(self) -> None:
        self._roles: Dict[str, Role] = {}
        self._user_roles: Dict[str, Set[str]] = {}

    def create_role(self, name: str, permissions: Optional[Set[Permission]] = None) -> Role:
        role = Role(name, permissions)
        self._roles[role.role_id] = role
        return role

    def assign_role(self, user_id: str, role_id: str) -> bool:
        if role_id in self._roles:
            self._user_roles.setdefault(user_id, set()).add(role_id)
            return True
        return False

    def revoke_role(self, user_id: str, role_id: str) -> bool:
        if user_id in self._user_roles:
            self._user_roles[user_id].discard(role_id)
            return True
        return False

    def has_permission(self, user_id: str, permission: Permission) -> bool:
        role_ids = self._user_roles.get(user_id, set())
        for rid in role_ids:
            role = self._roles.get(rid)
            if role and permission in role.permissions:
                return True
        return False

    def get_user_roles(self, user_id: str) -> List[str]:
        return list(self._user_roles.get(user_id, set()))

    def get_role_permissions(self, role_id: str) -> Set[Permission]:
        role = self._roles.get(role_id)
        return role.permissions if role else set()

    def list_roles(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._roles.values()]

    def stats(self) -> Dict[str, Any]:
        return {"roles": len(self._roles), "assignments": sum(len(v) for v in self._user_roles.values())}
