"""TokenManager — manage API tokens and session tokens."""
from __future__ import annotations
import secrets
import time
import uuid
from typing import Any, Dict, List, Optional
from enum import Enum


class TokenType(str, Enum):
    API_KEY = "api_key"; SESSION = "session"; REFRESH = "refresh"; BEARER = "bearer"


class Token:
    __slots__ = ("token_id", "token_value", "token_type", "user_id",
                 "created_at", "expires_at", "revoked", "metadata")

    def __init__(self, token_type: TokenType, user_id: str,
                 expires_in: float = 3600.0) -> None:
        self.token_id = str(uuid.uuid4())[:12]
        self.token_value = secrets.token_urlsafe(32)
        self.token_type = token_type
        self.user_id = user_id
        self.created_at = time.time()
        self.expires_at = time.time() + expires_in
        self.revoked = False
        self.metadata: Dict[str, Any] = {}

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def is_valid(self) -> bool:
        return not self.is_expired() and not self.revoked

    def to_dict(self) -> Dict[str, Any]:
        return {"token_id": self.token_id, "token_type": self.token_type.value,
                "user_id": self.user_id, "revoked": self.revoked}


class TokenManager:
    def __init__(self) -> None:
        self._tokens: Dict[str, Token] = {}
        self._user_tokens: Dict[str, List[str]] = {}

    def create_token(self, token_type: TokenType, user_id: str,
                     expires_in: float = 3600.0) -> Token:
        token = Token(token_type, user_id, expires_in)
        self._tokens[token.token_value] = token
        self._user_tokens.setdefault(user_id, []).append(token.token_value)
        return token

    def validate_token(self, token_value: str) -> Optional[Token]:
        token = self._tokens.get(token_value)
        if token and token.is_valid():
            return token
        return None

    def revoke_token(self, token_value: str) -> bool:
        token = self._tokens.get(token_value)
        if token:
            token.revoked = True
            return True
        return False

    def revoke_all_user_tokens(self, user_id: str) -> int:
        count = 0
        for tv in self._user_tokens.get(user_id, []):
            token = self._tokens.get(tv)
            if token and not token.revoked:
                token.revoked = True
                count += 1
        return count

    def list_tokens(self, user_id: Optional[str] = None,
                    token_type: Optional[TokenType] = None) -> List[Dict[str, Any]]:
        tokens = self._tokens.values()
        if user_id:
            tokens = [t for t in tokens if t.user_id == user_id]
        if token_type:
            tokens = [t for t in tokens if t.token_type == token_type]
        return [t.to_dict() for t in tokens]

    def cleanup_expired(self) -> int:
        expired = [tv for tv, t in self._tokens.items() if t.is_expired()]
        for tv in expired:
            del self._tokens[tv]
        return len(expired)

    def stats(self) -> Dict[str, Any]:
        active = sum(1 for t in self._tokens.values() if t.is_valid())
        return {"total": len(self._tokens), "active": active,
                "revoked": sum(1 for t in self._tokens.values() if t.revoked)}
