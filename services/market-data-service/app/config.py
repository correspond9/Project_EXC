from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://xchange:xchange@postgres:5432/xchange_db"
    DATABASE_SYNC_URL: str = "postgresql://xchange:xchange@postgres:5432/xchange_db"

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"

    # ── Binance ───────────────────────────────────────────────────────────────
    BINANCE_WS_BASE: str = "wss://stream.binance.com:9443/stream"
    BINANCE_REST_BASE: str = "https://api.binance.com"
    # Comma-separated list of Binance symbol names (no slash, uppercase)
    TRADING_SYMBOLS: str = (
        "BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT,XRPUSDT,"
        "ADAUSDT,DOGEUSDT,AVAXUSDT,DOTUSDT,MATICUSDT"
    )
    # Kline intervals to subscribe to on Binance WebSocket
    KLINE_INTERVALS: str = "1m,5m,1h,1d"

    # ── App ───────────────────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    @property
    def symbols_list(self) -> List[str]:
        return [s.strip().upper() for s in self.TRADING_SYMBOLS.split(",") if s.strip()]

    @property
    def intervals_list(self) -> List[str]:
        return [i.strip() for i in self.KLINE_INTERVALS.split(",") if i.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
