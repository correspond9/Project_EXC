import enum
import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID

from ..database import Base


class MarketType(str, enum.Enum):
    SPOT = "SPOT"
    FUTURES = "FUTURES"
    OPTIONS = "OPTIONS"


class TradingPair(Base):
    """
    Master list of all tradeable instruments on the platform.
    Populated by the seed script; referenced by orders, positions, price_history.
    """
    __tablename__ = "trading_pairs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Human-readable symbol e.g. BTC/USDT
    symbol = Column(String(20), nullable=False, unique=True, index=True)
    # Binance stream symbol e.g. BTCUSDT
    binance_symbol = Column(String(20), nullable=False, unique=True, index=True)
    base_asset = Column(String(10), nullable=False)
    quote_asset = Column(String(10), nullable=False)
    market_type = Column(
        SAEnum(MarketType, name="market_type"),
        nullable=False,
        default=MarketType.SPOT,
        server_default=MarketType.SPOT.value,
    )
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    # Trading constraints (from Binance exchange info, filled by seed script)
    min_quantity = Column(Numeric(30, 10), nullable=True)
    max_quantity = Column(Numeric(30, 10), nullable=True)
    price_tick_size = Column(Numeric(30, 10), nullable=True)
    quantity_step = Column(Numeric(30, 10), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PriceHistory(Base):
    """
    OHLCV candle data — one row per closed candle per symbol per interval.
    Persisted by the Binance WebSocket feed when a kline closes.
    """
    __tablename__ = "price_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False, index=True)
    interval = Column(String(5), nullable=False)
    open_time = Column(BigInteger, nullable=False)
    open_price = Column(Numeric(30, 10), nullable=False)
    high_price = Column(Numeric(30, 10), nullable=False)
    low_price = Column(Numeric(30, 10), nullable=False)
    close_price = Column(Numeric(30, 10), nullable=False)
    volume = Column(Numeric(30, 10), nullable=False)
    close_time = Column(BigInteger, nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("symbol", "interval", "open_time", name="uq_price_history"),
    )
