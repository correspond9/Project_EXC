"""
Seed Script — Trading Pairs
============================
Inserts the 10 initial SPOT trading pairs into the trading_pairs table.
Fetches live exchange info from Binance REST API to get accurate
min_quantity, max_quantity, price_tick_size, and quantity_step values.

Run inside the container:
  docker-compose exec market-data-service python scripts/seed_pairs.py

Or via Makefile:
  make seed
"""

import asyncio
import os
import sys

import httpx
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ── Config ────────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://xchange:xchange@postgres:5432/xchange_db",
)
BINANCE_REST_BASE = os.getenv("BINANCE_REST_BASE", "https://api.binance.com")

PAIRS = [
    {"symbol": "BTC/USDT",  "binance_symbol": "BTCUSDT",  "base": "BTC",  "quote": "USDT"},
    {"symbol": "ETH/USDT",  "binance_symbol": "ETHUSDT",  "base": "ETH",  "quote": "USDT"},
    {"symbol": "BNB/USDT",  "binance_symbol": "BNBUSDT",  "base": "BNB",  "quote": "USDT"},
    {"symbol": "SOL/USDT",  "binance_symbol": "SOLUSDT",  "base": "SOL",  "quote": "USDT"},
    {"symbol": "XRP/USDT",  "binance_symbol": "XRPUSDT",  "base": "XRP",  "quote": "USDT"},
    {"symbol": "ADA/USDT",  "binance_symbol": "ADAUSDT",  "base": "ADA",  "quote": "USDT"},
    {"symbol": "DOGE/USDT", "binance_symbol": "DOGEUSDT", "base": "DOGE", "quote": "USDT"},
    {"symbol": "AVAX/USDT", "binance_symbol": "AVAXUSDT", "base": "AVAX", "quote": "USDT"},
    {"symbol": "DOT/USDT",  "binance_symbol": "DOTUSDT",  "base": "DOT",  "quote": "USDT"},
    {"symbol": "MATIC/USDT","binance_symbol": "MATICUSDT","base": "MATIC","quote": "USDT"},
]


def _fetch_exchange_info() -> dict:
    """Fetch symbol constraints from Binance REST API (synchronous, run once)."""
    url = f"{BINANCE_REST_BASE}/api/v3/exchangeInfo"
    constraints = {}
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(url)
            resp.raise_for_status()
            info = resp.json()

        for s in info.get("symbols", []):
            sym = s.get("symbol", "")
            filters = {f["filterType"]: f for f in s.get("filters", [])}

            lot = filters.get("LOT_SIZE", {})
            price = filters.get("PRICE_FILTER", {})

            constraints[sym] = {
                "min_quantity": lot.get("minQty"),
                "max_quantity": lot.get("maxQty"),
                "quantity_step": lot.get("stepSize"),
                "price_tick_size": price.get("tickSize"),
            }
        print(f"  Fetched exchange info for {len(constraints)} symbols from Binance.")
    except Exception as exc:
        print(f"  WARNING: Could not fetch Binance exchange info: {exc}")
        print("  Trading pair constraints will be left as NULL.")
    return constraints


async def seed(engine) -> None:
    AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession)
    constraints = _fetch_exchange_info()

    # Import here to avoid circular deps when run as a script
    from sqlalchemy import Table, MetaData
    metadata = MetaData()
    await engine.run_sync(metadata.reflect)

    trading_pairs = metadata.tables.get("trading_pairs")
    if trading_pairs is None:
        print("ERROR: trading_pairs table not found. Run 'alembic upgrade head' first.")
        sys.exit(1)

    records = []
    for pair in PAIRS:
        c = constraints.get(pair["binance_symbol"], {})
        records.append({
            "symbol": pair["symbol"],
            "binance_symbol": pair["binance_symbol"],
            "base_asset": pair["base"],
            "quote_asset": pair["quote"],
            "market_type": "SPOT",
            "is_active": True,
            "min_quantity": c.get("min_quantity"),
            "max_quantity": c.get("max_quantity"),
            "price_tick_size": c.get("price_tick_size"),
            "quantity_step": c.get("quantity_step"),
        })

    async with AsyncSessionLocal() as session:
        stmt = (
            pg_insert(trading_pairs)
            .values(records)
            .on_conflict_do_update(
                index_elements=["symbol"],
                set_={
                    "is_active": True,
                    "min_quantity": pg_insert(trading_pairs).excluded.min_quantity,
                    "max_quantity": pg_insert(trading_pairs).excluded.max_quantity,
                    "price_tick_size": pg_insert(trading_pairs).excluded.price_tick_size,
                    "quantity_step": pg_insert(trading_pairs).excluded.quantity_step,
                },
            )
        )
        await session.execute(stmt)
        await session.commit()

    print(f"  Seeded {len(records)} trading pairs successfully.")


async def main() -> None:
    print("=== Seeding trading pairs ===")
    engine = create_async_engine(DATABASE_URL, echo=False)
    try:
        await seed(engine)
    finally:
        await engine.dispose()
    print("=== Done ===")


if __name__ == "__main__":
    asyncio.run(main())
