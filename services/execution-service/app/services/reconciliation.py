"""Periodic reconciliation: compare open orders in DB vs Binance.

Runs every RECONCILIATION_INTERVAL_SECONDS (default 300s). For each open LIVE
order found in the DB, checks Binance status. If filled or cancelled on Binance
but not yet in our DB, updates accordingly.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import AsyncSessionLocal
from ..models.order import ExecutionMode, Order, OrderStatus
from .binance_client import BinanceClient
from .order_router import LiveOrderRouter

logger = logging.getLogger(__name__)


async def reconcile_open_orders(router: LiveOrderRouter, client: BinanceClient) -> None:
    """Single reconciliation pass over open LIVE orders."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Order).where(
                Order.execution_mode == ExecutionMode.LIVE,
                Order.status.in_([OrderStatus.OPEN, OrderStatus.PENDING]),
                Order.external_order_id.isnot(None),
            )
        )
        open_orders = result.scalars().all()

    if not open_orders:
        return

    logger.info("Reconciliation: checking %d open LIVE orders", len(open_orders))
    for order in open_orders:
        try:
            if order.market_type.value == "FUTURES":
                raw = await client.fetch_futures_order(order.external_order_id, order.symbol)
            else:
                raw = await client.fetch_spot_order(order.external_order_id, order.symbol)

            binance_status = raw.get("status", "")
            if binance_status in ("closed", "filled"):
                logger.info("Reconciliation: order %s filled on Binance — recording", order.id)
                await router._record_fill(
                    order_id=order.id,
                    user_id=order.user_id,
                    raw=raw,
                    symbol=order.symbol,
                    market_type=order.market_type.value,
                )
            elif binance_status in ("canceled", "rejected", "expired"):
                logger.info("Reconciliation: order %s is %s on Binance", order.id, binance_status)
                await router._reject_order(order.id)
        except Exception as exc:
            logger.warning("Reconciliation error for order %s: %s", order.id, exc)


async def reconciliation_loop(router: LiveOrderRouter, client: BinanceClient) -> None:
    """Run reconciliation forever at the configured interval."""
    logger.info("Reconciliation loop started (interval=%ds)", settings.RECONCILIATION_INTERVAL_SECONDS)
    while True:
        await asyncio.sleep(settings.RECONCILIATION_INTERVAL_SECONDS)
        try:
            await reconcile_open_orders(router, client)
        except Exception as exc:
            logger.exception("Reconciliation loop error: %s", exc)
