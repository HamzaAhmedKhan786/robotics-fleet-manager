"""Shared fixtures for API integration tests."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from apps.backend.core.config import settings
from apps.backend.db.session import get_db
from apps.backend.main import app

TEST_DB_NAME = "robotics_fleet_test"


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create an API client connected only to the test database."""

    database_url = URL.create(
        drivername="postgresql+asyncpg",
        username=settings.postgres_user,
        password=settings.postgres_password.get_secret_value(),
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=TEST_DB_NAME,
    )

    test_engine = create_async_engine(database_url)

    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_db():
        async with test_session_factory() as session:
            yield session

    try:
        # Safety check before modifying any data.
        async with test_engine.connect() as connection:
            database = await connection.scalar(text("SELECT current_database()"))

        if database != TEST_DB_NAME:
            raise RuntimeError("Integration tests must use robotics_fleet_test.")

        app.dependency_overrides[get_db] = override_get_db

        # Remove records left by previous test runs.
        async with test_engine.begin() as connection:
            await connection.execute(text("DELETE FROM robots"))

        transport = ASGITransport(app=app)

        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as test_client:
            yield test_client

    finally:
        app.dependency_overrides.clear()

        # Clean up records created by the test.
        try:
            async with test_engine.begin() as connection:
                database = await connection.scalar(text("SELECT current_database()"))
                if database == TEST_DB_NAME:
                    await connection.execute(text("DELETE FROM robots"))
        finally:
            await test_engine.dispose()
