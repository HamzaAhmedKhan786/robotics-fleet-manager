"""Alembic migration environment."""

from logging.config import fileConfig

from sqlalchemy import URL, engine_from_config, pool

from alembic import context
from apps.backend.core.config import settings
from apps.backend.db.base import Base

# Import models so Alembic discovers their tables.
from apps.backend.models.robot import Robot  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Alembic compares models against the actual database.
target_metadata = Base.metadata

# Use psycopg for synchronous schema migrations.
# FastAPI continues using asyncpg for asynchronous queries.
database_url = URL.create(
    drivername="postgresql+psycopg",
    username=settings.postgres_user,
    password=settings.postgres_password.get_secret_value(),
    host=settings.postgres_host,
    port=settings.postgres_port,
    database=settings.postgres_db,
)


def run_migrations_offline() -> None:
    """Generate migrations without connecting to PostgreSQL."""
    context.configure(
        url=database_url.render_as_string(hide_password=False),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against PostgreSQL."""
    configuration = config.get_section(config.config_ini_section, {}).copy()

    configuration["sqlalchemy.url"] = database_url.render_as_string(hide_password=False)

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
