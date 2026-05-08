from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://xchange:xchange@postgres:5432/xchange_db"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"

    # Margin call threshold: alert when margin ratio falls below this %
    MARGIN_CALL_THRESHOLD_PCT: float = 20.0

    @property
    def margin_call_threshold(self) -> float:
        return self.MARGIN_CALL_THRESHOLD_PCT / 100.0


settings = Settings()
