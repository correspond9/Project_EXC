"""Syncs real wallet balances from Binance to the real_wallets table."""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .binance_client import BinanceClient

logger = logging.getLogger(__name__)

_ZERO = Decimal("0")


async def sync_spot_balances(
    db: AsyncSession, user_id: uuid.UUID, client: BinanceClient
) -> None:
    """Fetch Binance spot balances and upsert into real_wallets."""
    try:
        raw = await client.fetch_spot_balance()
    except Exception as exc:
        logger.warning("Balance sync failed for user %s: %s", user_id, exc)
        return

    totals: dict[str, Decimal] = {}
    for currency, info in raw.get("total", {}).items():
        amount = Decimal(str(info)) if info else _ZERO
        if amount > _ZERO:
            totals[currency.upper()] = amount

    for currency, total in totals.items():
        await _upsert_wallet(db, user_id, currency, total)

    await db.commit()
    logger.info("Synced %d spot balances for user %s", len(totals), user_id)


async def sync_futures_balances(
    db: AsyncSession, user_id: uuid.UUID, client: BinanceClient
) -> None:
    """Fetch Binance futures balances and upsert into real_wallets (USDT margin)."""
    try:
        raw = await client.fetch_futures_balance()
    except Exception as exc:
        logger.warning("Futures balance sync failed for user %s: %s", user_id, exc)
        return

    for currency, info in raw.get("total", {}).items():
        amount = Decimal(str(info)) if info else _ZERO
        if amount > _ZERO:
            await _upsert_wallet(db, user_id, currency.upper(), amount)

    await db.commit()


async def _upsert_wallet(
    db: AsyncSession, user_id: uuid.UUID, currency: str, total: Decimal
) -> None:
    result = await db.execute(
        text(
            "SELECT id FROM real_wallets WHERE user_id = :uid AND currency = :cur"
        ),
        {"uid": str(user_id), "cur": currency},
    )
    row = result.fetchone()
    if row:
        await db.execute(
            text(
                "UPDATE real_wallets SET balance = :bal, updated_at = now() "
                "WHERE user_id = :uid AND currency = :cur"
            ),
            {"bal": float(total), "uid": str(user_id), "cur": currency},
        )
    else:
        await db.execute(
            text(
                "INSERT INTO real_wallets (id, user_id, currency, balance, locked_balance) "
                "VALUES (gen_random_uuid(), :uid, :cur, :bal, 0)"
            ),
            {"uid": str(user_id), "cur": currency, "bal": float(total)},
        )
