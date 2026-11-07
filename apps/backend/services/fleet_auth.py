"""FleetOS local JWT authentication with database-backed user roles.

Use TLS, managed secrets, per-user accounts, lockout/rate-limit and external
identity provider for public production exposure.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash

from apps.backend.core.config import settings

_hash = PasswordHash.recommended()
_bearer = HTTPBearer(auto_error=False)
ROLES = {"viewer": 0, "operator": 1, "admin": 2}


def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters")
    return _hash.hash(password)


def verify_password(password: str, digest: str) -> bool:
    return _hash.verify(password, digest)


def issue_token(username: str, role: str) -> str:
    if role not in ROLES:
        raise ValueError("Unknown role")
    now = datetime.now(UTC)
    return jwt.encode({
        "sub": username, "role": role, "iss": "fleetos",
        "iat": now, "exp": now + timedelta(minutes=30),
    }, settings.jwt_secret.get_secret_value(), algorithm="HS256")


def verify_token(token: str) -> dict[str, str]:
    try:
        claims = jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=["HS256"], issuer="fleetos")
    except jwt.PyJWTError as exc:
        raise HTTPException(401, "Invalid or expired access token") from exc
    if claims.get("role") not in ROLES or not claims.get("sub"):
        raise HTTPException(401, "Invalid token claims")
    return {"username": str(claims["sub"]), "role": str(claims["role"])}


async def current_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]) -> dict[str, str]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "Bearer authentication required")
    return verify_token(credentials.credentials)


def require_role(role: str):
    async def checker(user: Annotated[dict[str, str], Depends(current_user)]) -> str:
        if ROLES[user["role"]] < ROLES[role]:
            raise HTTPException(403, "Insufficient role")
        return user["username"]
    return checker
