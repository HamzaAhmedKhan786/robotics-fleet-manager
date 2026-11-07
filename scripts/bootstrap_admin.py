"""One-time admin provisioning in local PostgreSQL, using password prompt.

Run after migrations: pixi run python -m scripts.bootstrap_admin
"""
import asyncio
from getpass import getpass

from sqlalchemy import text

from apps.backend.db.session import AsyncSessionLocal
from apps.backend.services.fleet_auth import hash_password


async def create(username: str, password: str) -> None:
    if not (3 <= len(username) <= 80):
        raise ValueError("Username must be 3-80 characters")
    digest = hash_password(password)
    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(text("""
            INSERT INTO fleet_users(username, password_hash, role)
            VALUES (:name, :digest, 'admin')
            ON CONFLICT(username) DO NOTHING
        """), {"name": username, "digest": digest})
    print("Bootstrap finished. Existing usernames are never overwritten.")


if __name__ == "__main__":
    username = input("Admin username: ").strip()
    password = getpass("Admin password (12+ chars): ")
    asyncio.run(create(username, password))
