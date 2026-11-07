"""Local identity endpoints: password login and user management by administrators."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.db.session import get_db
from apps.backend.services.fleet_auth import (
    ROLES,
    hash_password,
    issue_token,
    require_role,
    verify_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Identity"])
Session = Annotated[AsyncSession, Depends(get_db)]
Admin = Annotated[str, Depends(require_role("admin"))]


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str


class NewUser(Credentials):
    role: str = "viewer"


@router.post("/login")
async def login(credentials: Credentials, session: Session):
    row = (await session.execute(text("""
        SELECT username, password_hash, role, enabled
        FROM fleet_users WHERE username = :username
    """), {"username": credentials.username})).mappings().first()
    if row is None or not row["enabled"] or not verify_password(credentials.password, row["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": issue_token(row["username"], row["role"]), "token_type": "bearer", "role": row["role"]}


@router.post("/users", status_code=201)
async def create_user(data: NewUser, session: Session, actor: Admin):
    if data.role not in ROLES:
        raise HTTPException(422, "Unknown role")
    digest = hash_password(data.password)
    async with session.begin():
        existed = await session.scalar(text("SELECT 1 FROM fleet_users WHERE username = :username"), {"username": data.username})
        if existed:
            raise HTTPException(409, "Username already exists")
        await session.execute(text("""
            INSERT INTO fleet_users(username, password_hash, role)
            VALUES (:username, :password_hash, :role)
        """), {"username": data.username, "password_hash": digest, "role": data.role})
        await session.execute(text("""
            INSERT INTO fleet_audit_events(actor, action, resource)
            VALUES (:actor, 'create_user', :resource)
        """), {"actor": actor, "resource": data.username})
    return {"username": data.username, "role": data.role}
