import json
from typing import List, Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.market import PriceHistory, TradingPair
from ..redis_client import get_redis
from ..schemas.market import (
    KlineResponse,
    OrderBookResponse,
    TickerResponse,
    TradingPairResponse,
)

router = APIRouter(prefix="/api/market", tags=["Market Data"])

_VALID_INTERVALS = {"1m", "5m", "1h", "1d"}


# ── GET /api/market/pairs ─────────────────────────────────────────────────────

@router.get("/pairs", response_model=List[TradingPairResponse])
async def get_trading_pairs(
    db: AsyncSession = Depends(get_db),
) -> List[TradingPair]:
    result = await db.execute(
        select(TradingPair)
        .where(TradingPair.is_active == True)  # noqa: E712
        .order_by(TradingPair.symbol)
    )
    return result.scalars().all()


# ── GET /api/market/ticker/{symbol} ──────────────────────────────────────────

@router.get("/ticker/{symbol}", response_model=TickerResponse)
async def get_ticker(
    symbol: str,
    redis: aioredis.Redis = Depends(get_redis),
) -> TickerResponse:
    symbol = symbol.upper()
    raw = await redis.get(f"ticker:{symbol}")
    if raw is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No ticker data found for {symbol}. "
                   f"The Binance feed may still be starting up.",
        )
    data = json.loads(raw)
    return TickerResponse(
        symbol=data["symbol"],
        last_price=data["last_price"],
        open_price=data["open_price"],
        high_price=data["high_price"],
        low_price=data["low_price"],
        volume=data["volume"],
        price_change=data["price_change"],
        price_change_pct=data["price_change_pct"],
        updated_at_ms=data["ts"],
    )


# ── GET /api/market/orderbook/{symbol} ───────────────────────────────────────

@router.get("/orderbook/{symbol}", response_model=OrderBookResponse)
async def get_orderbook(
    symbol: str,
    redis: aioredis.Redis = Depends(get_redis),
) -> OrderBookResponse:
    symbol = symbol.upper()
    raw = await redis.get(f"orderbook:{symbol}")
    if raw is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No order book data found for {symbol}. "
                   f"The Binance feed may still be starting up.",
        )
    data = json.loads(raw)
    return OrderBookResponse(
        symbol=data["symbol"],
        bids=data["bids"],
        asks=data["asks"],
        updated_at_ms=data["ts"],
    )


# ── GET /api/market/klines/{symbol} ──────────────────────────────────────────

@router.get("/klines/{symbol}", response_model=List[KlineResponse])
async def get_klines(
    symbol: str,
    interval: str = Query("1h", description="Candle interval: 1m, 5m, 1h, 1d"),
    limit: int = Query(200, ge=1, le=1000, description="Number of candles to return"),
    db: AsyncSession = Depends(get_db),
) -> List[KlineResponse]:
    symbol = symbol.upper()

    if interval not in _VALID_INTERVALS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid interval '{interval}'. Valid options: {sorted(_VALID_INTERVALS)}",
        )

    result = await db.execute(
        select(PriceHistory)
        .where(
            PriceHistory.symbol == symbol,
            PriceHistory.interval == interval,
        )
        .order_by(PriceHistory.open_time.desc())
        .limit(limit)
    )
    rows = result.scalars().all()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No candle data found for {symbol}/{interval}. "
                   f"Run the backfill script to load historical data.",
        )

    # Return in ascending time order (oldest first)
    return [
        KlineResponse(
            symbol=row.symbol,
            interval=row.interval,
            open_time=row.open_time,
            open=str(row.open_price),
            high=str(row.high_price),
            low=str(row.low_price),
            close=str(row.close_price),
            volume=str(row.volume),
            close_time=row.close_time,
        )
        for row in reversed(rows)
    ]
