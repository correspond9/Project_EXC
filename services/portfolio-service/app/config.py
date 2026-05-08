from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://xchange:xchange@postgres:5432/xchange_db"
    DATABASE_SYNC_URL: str = "postgresql://xchange:xchange@postgres:5432/xchange_db"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"

    TRADING_SYMBOLS: str = (
        "BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT,XRPUSDT,"
        "ADAUSDT,DOGEUSDT,AVAXUSDT,DOTUSDT,MATICUSDT"
    )

    @property
    def symbols_list(self) -> list[str]:
        return [s.strip().upper() for s in self.TRADING_SYMBOLS.split(",") if s.strip()]


settings = Settings()
