from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://xchange:xchange@postgres:5432/xchange_db"
    DATABASE_SYNC_URL: str = "postgresql://xchange:xchange@postgres:5432/xchange_db"

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Compliance / KYC ─────────────────────────────────────────────────────
    KYC_WEBHOOK_SECRET: str = ""
    AML_PROVIDER_URL: str = ""
    AML_PROVIDER_API_KEY: str = ""
    AML_RISK_REVIEW_THRESHOLD: float = 70.0

    # ── App ───────────────────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    DEBUG: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
