"""Centralized application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Validated application settings loaded from the environment."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Robotics Fleet Manager"
    app_env: str = "development"
    log_level: str = "INFO"

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    postgres_db: str = "robotics_fleet"
    postgres_user: str = "postgres"
    postgres_password: SecretStr

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Authentication — implementation planned
    jwt_secret: SecretStr
    jwt_algorithm: str = "HS256"

    # Robot simulation — implementation planned
    simulation_enabled: bool = True
    simulation_robot_count: int = Field(default=5, ge=0)
    simulation_tick_seconds: float = Field(default=1.0, gt=0)


@lru_cache
def get_settings() -> Settings:
    """Create and cache the validated application settings."""
    return Settings()  # pyright: ignore[reportCallIssue]


settings = get_settings()
