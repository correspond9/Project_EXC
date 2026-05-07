"""
Backfill Script — Historical OHLCV Data
=========================================
Loads 30 days of historical kline (candlestick) data for all 10 trading pairs
from Binance REST API and inserts them into the price_history table.

Intervals loaded: 1m, 5m, 1h, 1d

Binance /api/v3/klines returns up to 1000 candles per request.
This script pages through the data automatically until 30 days are covered.

Run inside the container (one-time, takes ~2-3 minutes):
  docker-compose exec market-data-service python scripts/backfill_ohlcv.py

Optional: limit to specific symbols or intervals:
  BACKFILL_SYMBOLS=BTCUSDT,ETHUSDT python scripts/backfill_ohlcv.py
  BACKFILL_INTERVALS=1h,1d python scripts/backfill_ohlcv.py
"""

import asyncio
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import httpx


# ── Token-bucket rate limiter ─────────────────────────────────────────────────
# Target: ≤ 1,200 weight per minute — a conservative 20% of Binance's current
# 6,000/min hard limit.  Each /api/v3/klines call costs 2 weight.
# See docs/BINANCE_RATE_LIMITS.md for full details.

class TokenBucket:
    """
    Async token-bucket rate limiter.

    capacity : float — maximum tokens the bucket can hold (burst ceiling)
    rate     : float — tokens added per second
    """

    def __init__(self, capacity: float, rate: float) -> None:
        self.capacity = float(capacity)
        self.rate = float(rate)
        self._tokens: float = float(capacity)
        self._last_refill: float = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: float = 1.0) -> None:
        """Block until `tokens` are available, then consume them."""
        while True:
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self._last_refill
                self._tokens = min(
                    self.capacity, self._tokens + elapsed * self.rate
                )
                self._last_refill = now

                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return

                deficit = tokens - self._tokens
                wait = deficit / self.rate

            # Sleep outside the lock so other coroutines are not blocked
            await asyncio.sleep(wait)


from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ── Config ────────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://xchange:xchange@postgres:5432/xchange_db",
)
BINANCE_REST_BASE = os.getenv("BINANCE_REST_BASE", "https://api.binance.com")
BACKFILL_DAYS = int(os.getenv("BACKFILL_DAYS", "30"))

_env_symbols = os.getenv("BACKFILL_SYMBOLS", "")
SYMBOLS = (
    [s.strip().upper() for s in _env_symbols.split(",") if s.strip()]
    if _env_symbols
    else [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
        "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT",
    ]
)

_env_intervals = os.getenv("BACKFILL_INTERVALS", "")
INTERVALS = (
    [i.strip() for i in _env_intervals.split(",") if i.strip()]
    if _env_intervals
    else ["1m", "5m", "1h", "1d"]
)

LIMIT = 1000  # Binance max per request


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _days_ago_ms(days: int) -> int:
    dt = datetime.now(timezone.utc) - timedelta(days=days)
    return int(dt.timestamp() * 1000)


# Weight cost of a single /api/v3/klines request (per Binance docs)
_KLINES_WEIGHT = 2


async def _fetch_klines(
    client: httpx.AsyncClient,
    limiter: TokenBucket,
    symbol: str,
    interval: str,
    start_ms: int,
    end_ms: int,
) -> list:
    """Fetch one page of klines from Binance REST API, rate-limited."""
    await limiter.acquire(tokens=_KLINES_WEIGHT)

    resp = await client.get(
        f"{BINANCE_REST_BASE}/api/v3/klines",
        params={
            "symbol": symbol,
            "interval": interval,
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": LIMIT,
        },
        timeout=30,
    )

    if resp.status_code == 429:
        retry_after = int(resp.headers.get("Retry-After", 60))
        print(f"\n  [RATE LIMIT 429] Binance asked us to back off. "
              f"Sleeping {retry_after}s ...", flush=True)
        await asyncio.sleep(retry_after)
        raise RuntimeError("Rate limit 429 — will retry")

    if resp.status_code == 418:
        retry_after = int(resp.headers.get("Retry-After", 300))
        print(f"\n  [IP BAN 418] Binance has temporarily banned our IP. "
              f"Sleeping {retry_after}s ...", flush=True)
        await asyncio.sleep(retry_after)
        raise RuntimeError("IP ban 418 — will retry")

    resp.raise_for_status()
    return resp.json()


async def backfill_symbol_interval(
    session_factory,
    client: httpx.AsyncClient,
    limiter: TokenBucket,
    symbol: str,
    interval: str,
) -> int:
    """Backfill all candles for one symbol/interval combination. Returns count inserted."""
    from sqlalchemy import Table, MetaData
    from sqlalchemy.ext.asyncio import AsyncEngine

    start_ms = _days_ago_ms(BACKFILL_DAYS)
    end_ms = _now_ms()
    total_inserted = 0

    current_start = start_ms
    while current_start < end_ms:
        try:
            raw = await _fetch_klines(
                client, limiter, symbol, interval, current_start, end_ms
            )
        except (httpx.HTTPStatusError, RuntimeError) as exc:
            print(f"    ERROR fetching {symbol}/{interval}: {exc}")
            break

        if not raw:
            break

        records = [
            {
                "symbol": symbol,
                "interval": interval,
                "open_time": int(row[0]),
                "open_price": str(row[1]),
                "high_price": str(row[2]),
                "low_price": str(row[3]),
                "close_price": str(row[4]),
                "volume": str(row[5]),
                "close_time": int(row[6]),
            }
            for row in raw
        ]

        async with session_factory() as session:
            # Build insert from table object via reflection
            stmt = pg_insert(PriceHistoryTable).values(records)
            stmt = stmt.on_conflict_do_nothing(constraint="uq_price_history")
            result = await session.execute(stmt)
            await session.commit()
            total_inserted += result.rowcount

        # Advance to next page (last candle open_time + 1ms)
        last_open_time = int(raw[-1][0])
        current_start = last_open_time + 1

        if len(raw) < LIMIT:
            break  # No more pages

    return total_inserted


# Module-level table reference (populated in main after engine reflection)
PriceHistoryTable = None


async def main() -> None:
    global PriceHistoryTable

    print(f"=== OHLCV Backfill — {BACKFILL_DAYS} days ===")
    print(f"  Symbols   : {', '.join(SYMBOLS)}")
    print(f"  Intervals : {', '.join(INTERVALS)}")
    print()

    engine = create_async_engine(DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession)

    # Reflect the price_history table for use in pg_insert
    from sqlalchemy import MetaData, Table
    metadata = MetaData()
    await engine.run_sync(metadata.reflect)
    PriceHistoryTable = metadata.tables.get("price_history")

    if PriceHistoryTable is None:
        print("ERROR: price_history table not found. Run 'alembic upgrade head' first.")
        await engine.dispose()
        sys.exit(1)

    # Token bucket: capacity=1200 weight, rate=20 weight/sec → ≤1,200 weight/min
    # See docs/BINANCE_RATE_LIMITS.md for rationale.
    limiter = TokenBucket(capacity=1200, rate=20)

    async with httpx.AsyncClient() as client:
        for symbol in SYMBOLS:
            for interval in INTERVALS:
                print(f"  Backfilling {symbol} / {interval} ...", end=" ", flush=True)
                count = await backfill_symbol_interval(
                    session_factory, client, limiter, symbol, interval
                )
                print(f"{count} rows inserted.")

    await engine.dispose()
    print()
    print("=== Backfill complete ===")


if __name__ == "__main__":
    asyncio.run(main())
