import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://xchange:xchange@postgres:5432/xchange_db"
    DATABASE_SYNC_URL: str = "postgresql://xchange:xchange@postgres:5432/xchange_db"
    REDIS_URL: str = "redis://redis:6379/0"

    # JWT — must match user-service secret for token verification
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"

    # Initial simulation wallet balance granted to new users (USDT)
    DEFAULT_SIMULATION_BALANCE: str = "0"


settings = Settings()
