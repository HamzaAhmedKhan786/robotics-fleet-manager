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
    """Provide an HTTP client using only the disposable test database."""

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

    async def clean_test_data():
        async with test_engine.begin() as connection:
            database = await connection.scalar(text("SELECT current_database()"))

            if database != TEST_DB_NAME:
                raise RuntimeError("Refusing to clean a non-test database.")

            # Delete dependent records before parent records.
            await connection.execute(text("DELETE FROM missions"))
            await connection.execute(text("DELETE FROM robots"))

    try:
        # Verify the database identity before any deletion.
        async with test_engine.connect() as connection:
            database = await connection.scalar(text("SELECT current_database()"))

        if database != TEST_DB_NAME:
            raise RuntimeError("Integration tests require robotics_fleet_test.")

        await clean_test_data()

        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)

        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as test_client:
            yield test_client

    finally:
        app.dependency_overrides.pop(get_db, None)

        try:
            await clean_test_data()
        finally:
            await test_engine.dispose()
