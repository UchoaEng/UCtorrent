from __future__ import annotations

import secrets
from dataclasses import dataclass, field

from fastapi import Depends, Header, HTTPException, status


@dataclass
class AuthService:
    username: str
    password: str
    tokens: set[str] = field(default_factory=set)

    def login(self, username: str, password: str) -> str:
        if username != self.username or password != self.password:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais invalidas")
        token = secrets.token_urlsafe(32)
        self.tokens.add(token)
        return token

    def logout(self, token: str) -> None:
        self.tokens.discard(token)

    def require_token(self, authorization: str | None = Header(default=None)) -> str:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente")
        token = authorization.split(" ", 1)[1]
        if token not in self.tokens:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido")
        return token


auth_service = AuthService(username="admin", password="admin")


def require_auth(token: str = Depends(auth_service.require_token)) -> str:
    return token

