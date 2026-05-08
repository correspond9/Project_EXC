"""Configuration settings for execution-service."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://xchange:xchange@postgres:5432/xchange_db"
    DATABASE_SYNC_URL: str = "postgresql://xchange:xchange@postgres:5432/xchange_db"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"

    # Binance API credentials — must be set in production via env vars
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""
    # Safety: always default to testnet until explicitly disabled
    BINANCE_TESTNET: bool = True

    # How long to poll Binance for a fill (seconds)
    ORDER_POLL_TIMEOUT_SECONDS: int = 1800
    ORDER_POLL_INTERVAL_SECONDS: int = 3

    # Reconciliation interval (seconds)
    RECONCILIATION_INTERVAL_SECONDS: int = 300

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
