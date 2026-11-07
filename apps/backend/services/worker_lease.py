"""PostgreSQL transaction advisory lock for single active simulation scheduler.

All scheduler replicas may run; only one obtains the lock per tick.
No external leases or Redis service required.
"""
import os
import socket

from sqlalchemy import text

from apps.backend.db.session import AsyncSessionLocal

LOCK_ID = 2026110705


async def run_exclusive_tick(tick) -> bool:
    async with AsyncSessionLocal() as session, session.begin():
        acquired = await session.scalar(
            text("SELECT pg_try_advisory_xact_lock(:lock)"), {"lock": LOCK_ID}
        )
        if not acquired:
            return False
        await tick()
        owner = f"{socket.gethostname()}:{os.getpid()}"
        await session.execute(text("""
            INSERT INTO fleet_worker_status(id, owner, heartbeat_at)
            VALUES (1, :owner, now())
            ON CONFLICT(id) DO UPDATE SET
                owner = EXCLUDED.owner,
                heartbeat_at = EXCLUDED.heartbeat_at
        """), {"owner": owner})
        return True
