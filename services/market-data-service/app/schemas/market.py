from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ..models.market import MarketType


# ── Trading Pair ──────────────────────────────────────────────────────────────

class TradingPairResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    symbol: str
    binance_symbol: str
    base_asset: str
    quote_asset: str
    market_type: MarketType
    is_active: bool
    min_quantity: Optional[Decimal] = None
    max_quantity: Optional[Decimal] = None
    price_tick_size: Optional[Decimal] = None
    quantity_step: Optional[Decimal] = None


# ── Ticker ────────────────────────────────────────────────────────────────────

class TickerResponse(BaseModel):
    symbol: str
    last_price: str
    open_price: str
    high_price: str
    low_price: str
    volume: str
    price_change: str
    price_change_pct: str
    # Timestamp (ms) of when this ticker was last updated
    updated_at_ms: int


# ── Order Book ────────────────────────────────────────────────────────────────

class OrderBookResponse(BaseModel):
    symbol: str
    # Each entry: [price, quantity] as strings
    bids: List[List[str]]
    asks: List[List[str]]
    updated_at_ms: int


# ── Kline / OHLCV ─────────────────────────────────────────────────────────────

class KlineResponse(BaseModel):
    symbol: str
    interval: str
    open_time: int
    open: str
    high: str
    low: str
    close: str
    volume: str
    close_time: int


# ── Live feed message (published to Redis pub/sub + sent over WebSocket) ──────

class TickerMessage(BaseModel):
    """Normalised ticker message published to Redis and forwarded to WebSocket clients."""
    type: str = "ticker"
    symbol: str
    last_price: str
    open_price: str
    high_price: str
    low_price: str
    volume: str
    price_change: str
    price_change_pct: str
    ts: int


class KlineMessage(BaseModel):
    """Normalised kline message published to Redis and forwarded to WebSocket clients."""
    type: str = "kline"
    symbol: str
    interval: str
    open_time: int
    open: str
    high: str
    low: str
    close: str
    volume: str
    close_time: int
    is_closed: bool


class OrderBookMessage(BaseModel):
    """Normalised order book message published to Redis and forwarded to WebSocket clients."""
    type: str = "orderbook"
    symbol: str
    bids: List[List[str]]
    asks: List[List[str]]
    ts: int
