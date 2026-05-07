from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://xchange:xchange@postgres:5432/xchange_db"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"

    # Comma-separated Binance-style symbols (no slash)
    TRADING_SYMBOLS: str = (
        "BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT,XRPUSDT,"
        "ADAUSDT,DOGEUSDT,AVAXUSDT,DOTUSDT,MATICUSDT"
    )

    # Taker fee applied to every simulated fill
    SIM_FEE_RATE: float = 0.001  # 0.1 %

    # How many top levels must change before a partial-fill watcher is woken
    BOOK_CHANGE_DEPTH: int = 3

    @property
    def symbols_list(self) -> list[str]:
        return [s.strip().upper() for s in self.TRADING_SYMBOLS.split(",") if s.strip()]


settings = Settings()
