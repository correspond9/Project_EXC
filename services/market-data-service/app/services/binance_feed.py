"""
Binance WebSocket Feed
======================
Connects to Binance's combined stream endpoint and subscribes to:
  - <symbol>@ticker        — 24h rolling price stats
  - <symbol>@depth20@1000ms — order book top 20 bid/ask levels (1s updates)
  - <symbol>@kline_1m      — 1-minute candles
  - <symbol>@kline_5m      — 5-minute candles
  - <symbol>@kline_1h      — 1-hour candles
  - <symbol>@kline_1d      — 1-day candles

On each message:
  - Normalise into our schema
  - Cache in Redis (key: ticker:<SYMBOL>, orderbook:<SYMBOL>, kline:<SYMBOL>:<INTERVAL>)
  - Publish to Redis Pub/Sub (channel: market.ticker.<SYMBOL>, etc.)
  - On kline close: persist OHLCV row to price_history table

Reconnection: exponential backoff (1s → 2s → 4s → ... → max 60s).
"""

import asyncio
import json
import logging
import time
from typing import Optional

import redis.asyncio as aioredis
import websockets
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..config import get_settings
from ..database import AsyncSessionLocal
from ..models.market import PriceHistory
from ..redis_client import get_redis_pool
from ..schemas.market import KlineMessage, OrderBookMessage, TickerMessage

logger = logging.getLogger(__name__)
settings = get_settings()

# Redis key prefixes
_TICKER_KEY = "ticker:{symbol}"
_ORDERBOOK_KEY = "orderbook:{symbol}"
_KLINE_KEY = "kline:{symbol}:{interval}"
# Redis TTL for cached data (seconds) — if feed is down, stale data expires
_CACHE_TTL = 300  # 5 minutes

# Redis Pub/Sub channel names
_TICKER_CHANNEL = "market.ticker.{symbol}"
_ORDERBOOK_CHANNEL = "market.orderbook.{symbol}"
_KLINE_CHANNEL = "market.kline.{symbol}.{interval}"


def _build_stream_url() -> str:
    """
    Build the Binance combined stream URL for all configured symbols and intervals.
    Example output:
      wss://stream.binance.com:9443/stream?streams=btcusdt@ticker/btcusdt@depth20@1000ms/...
    """
    streams = []
    for symbol in settings.symbols_list:
        sym_lower = symbol.lower()
        streams.append(f"{sym_lower}@ticker")
        streams.append(f"{sym_lower}@depth20@1000ms")
        for interval in settings.intervals_list:
            streams.append(f"{sym_lower}@kline_{interval}")
    return f"{settings.BINANCE_WS_BASE}?streams={'/'.join(streams)}"


# ── Message handlers ──────────────────────────────────────────────────────────

async def _handle_ticker(data: dict, redis: aioredis.Redis) -> None:
    symbol: str = data.get("s", "").upper()
    if not symbol:
        return

    msg = TickerMessage(
        symbol=symbol,
        last_price=data.get("c", "0"),
        open_price=data.get("o", "0"),
        high_price=data.get("h", "0"),
        low_price=data.get("l", "0"),
        volume=data.get("v", "0"),
        price_change=data.get("p", "0"),
        price_change_pct=data.get("P", "0"),
        ts=int(time.time() * 1000),
    )
    payload = msg.model_dump_json()

    key = _TICKER_KEY.format(symbol=symbol)
    channel = _TICKER_CHANNEL.format(symbol=symbol)
    async with redis.pipeline(transaction=False) as pipe:
        pipe.setex(key, _CACHE_TTL, payload)
        pipe.publish(channel, payload)
        await pipe.execute()


async def _handle_kline(data: dict, redis: aioredis.Redis) -> None:
    kline: dict = data.get("k", {})
    symbol: str = data.get("s", "").upper()
    interval: str = kline.get("i", "")
    is_closed: bool = kline.get("x", False)

    msg = KlineMessage(
        symbol=symbol,
        interval=interval,
        open_time=kline.get("t", 0),
        open=kline.get("o", "0"),
        high=kline.get("h", "0"),
        low=kline.get("l", "0"),
        close=kline.get("c", "0"),
        volume=kline.get("v", "0"),
        close_time=kline.get("T", 0),
        is_closed=is_closed,
    )
    payload = msg.model_dump_json()

    key = _KLINE_KEY.format(symbol=symbol, interval=interval)
    channel = _KLINE_CHANNEL.format(symbol=symbol, interval=interval)
    async with redis.pipeline(transaction=False) as pipe:
        pipe.setex(key, _CACHE_TTL, payload)
        pipe.publish(channel, payload)
        await pipe.execute()

    if is_closed:
        await _persist_kline(msg)


async def _persist_kline(msg: KlineMessage) -> None:
    """Insert a closed kline into price_history. Uses INSERT ... ON CONFLICT DO NOTHING."""
    async with AsyncSessionLocal() as session:
        try:
            stmt = (
                pg_insert(PriceHistory)
                .values(
                    symbol=msg.symbol,
                    interval=msg.interval,
                    open_time=msg.open_time,
                    open_price=msg.open,
                    high_price=msg.high,
                    low_price=msg.low,
                    close_price=msg.close,
                    volume=msg.volume,
                    close_time=msg.close_time,
                )
                .on_conflict_do_nothing(constraint="uq_price_history")
            )
            await session.execute(stmt)
            await session.commit()
        except Exception as exc:
            await session.rollback()
            logger.error("Failed to persist kline %s/%s: %s", msg.symbol, msg.interval, exc)


async def _handle_depth(stream_name: str, data: dict, redis: aioredis.Redis) -> None:
    # Stream name format: btcusdt@depth20@1000ms
    symbol = stream_name.split("@")[0].upper()

    msg = OrderBookMessage(
        symbol=symbol,
        bids=data.get("bids", [])[:20],
        asks=data.get("asks", [])[:20],
        ts=int(time.time() * 1000),
    )
    payload = msg.model_dump_json()

    key = _ORDERBOOK_KEY.format(symbol=symbol)
    channel = _ORDERBOOK_CHANNEL.format(symbol=symbol)
    async with redis.pipeline(transaction=False) as pipe:
        pipe.setex(key, _CACHE_TTL, payload)
        pipe.publish(channel, payload)
        await pipe.execute()


# ── Main feed loop ────────────────────────────────────────────────────────────

async def _process_message(raw: str, redis: aioredis.Redis) -> None:
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError:
        return

    stream: str = envelope.get("stream", "")
    data: dict = envelope.get("data", {})
    event_type: str = data.get("e", "")

    if event_type == "24hrTicker":
        await _handle_ticker(data, redis)
    elif event_type == "kline":
        await _handle_kline(data, redis)
    elif "depth" in stream:
        await _handle_depth(stream, data, redis)


async def run_binance_feed() -> None:
    """
    Main entry point — called as an asyncio background task from main.py lifespan.
    Connects to Binance combined stream and processes messages forever.
    Reconnects automatically with exponential backoff on any error.
    """
    url = _build_stream_url()
    backoff = 1.0

    logger.info(
        "Binance feed starting — %d symbols, %d intervals",
        len(settings.symbols_list),
        len(settings.intervals_list),
    )

    while True:
        try:
            redis = await get_redis_pool()
            logger.info("Connecting to Binance WebSocket...")

            async with websockets.connect(
                url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5,
            ) as ws:
                logger.info("Binance WebSocket connected. Receiving market data.")
                backoff = 1.0  # Reset backoff after successful connect

                async for message in ws:
                    await _process_message(message, redis)

        except asyncio.CancelledError:
            logger.info("Binance feed task cancelled. Shutting down.")
            break
        except Exception as exc:
            logger.warning(
                "Binance WebSocket error: %s. Reconnecting in %.0fs...", exc, backoff
            )
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60.0)
