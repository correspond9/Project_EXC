"""
Market order handler.

Fills a MARKET order immediately against the current order book snapshot.
If partially filled, spawns a background task that awaits the next meaningful
book refresh and retries until fully filled (or the order is cancelled).
"""
import asyncio
import logging
import uuid
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import AsyncSessionLocal
from ..models.order import Order, OrderStatus
from ..services.fill_engine import depth_walk
from ..services.handler_utils import (
    load_order,
    parse_currencies,
    persist_fills,
    publish_fill_event,
    symbol_to_redis_key,
)
from ..services.order_book_mirror import OrderBookMirror
from ..services.wallet_ops import apply_buy_fill, apply_sell_fill, release_locked_balance

log = logging.getLogger(__name__)

FEE_RATE = Decimal(str(settings.SIM_FEE_RATE))
MAX_WAIT_ITERATIONS = 200   # give up after this many book refreshes with no fill


async def handle_market_order(
    order_msg: dict,
    mirror: OrderBookMirror,
    redis_client,
) -> None:
    """Entry point called by order_subscriber for MARKET execution_mode=SIMULATION orders."""
    order_id = uuid.UUID(order_msg["order_id"])
    redis_sym = symbol_to_redis_key(order_msg["symbol"])
    book = mirror.get_book(redis_sym)

    async with AsyncSessionLocal() as db:
        order = await load_order(db, order_id)
        if order is None:
            log.warning("market_handler: order %s not found", order_id)
            return

        # Mark OPEN immediately so it's visible to the user
        order.status = OrderStatus.OPEN
        await db.flush()

        if book is None:
            log.warning("market_handler: no book snapshot for %s — rejecting order", redis_sym)
            order.status = OrderStatus.REJECTED
            await db.commit()
            await publish_fill_event(redis_client, order, None, "REJECTED")
            return

        remaining = Decimal(str(order.quantity))
        fills, remaining = depth_walk(book, order.side.value, remaining, FEE_RATE)

        if fills:
            base_cur, quote_cur = parse_currencies(order.symbol)
            for f in fills:
                if order.side.value == "BUY":
                    await apply_buy_fill(db, order.user_id, base_cur, quote_cur,
                                         f.fill_price, f.fill_quantity, f.fee)
                else:
                    await apply_sell_fill(db, order.user_id, base_cur, quote_cur,
                                          f.fill_price, f.fill_quantity, f.fee)

            await persist_fills(db, order, fills, remaining)
            await db.commit()

            # Publish a fill event for each fill row
            await db.refresh(order)
            for fill_row in order.fills[-len(fills):]:
                await publish_fill_event(redis_client, order, fill_row, order.status.value)

        if remaining > Decimal("0"):
            # Partial fill — watch for book updates and retry
            asyncio.create_task(
                _watch_and_complete(order_id, order.symbol, remaining, mirror, redis_client)
            )
        elif order.side.value == "BUY":
            # Release any over-reserved locked balance
            total_cost = sum(f.fill_price * f.fill_quantity + f.fee for f in fills)
            _, quote_cur = parse_currencies(order.symbol)
            reserved = Decimal(str(order.quantity)) * (
                Decimal(str(order_msg.get("price") or "0")) or
                (fills[0].fill_price * Decimal("1.01") if fills else Decimal("0"))
            )
            over_reserved = reserved - total_cost
            if over_reserved > Decimal("0"):
                async with AsyncSessionLocal() as db2:
                    await release_locked_balance(db2, order.user_id, quote_cur, over_reserved)
                    await db2.commit()


async def _watch_and_complete(
    order_id: uuid.UUID,
    symbol: str,
    remaining: Decimal,
    mirror: OrderBookMirror,
    redis_client,
) -> None:
    """Background task: waits for book updates and retries fills until completed."""
    redis_sym = symbol_to_redis_key(symbol)
    q = mirror.subscribe_book(redis_sym)
    try:
        iteration = 0
        while remaining > Decimal("0") and iteration < MAX_WAIT_ITERATIONS:
            iteration += 1
            try:
                book = await asyncio.wait_for(q.get(), timeout=60.0)
            except asyncio.TimeoutError:
                continue

            async with AsyncSessionLocal() as db:
                order = await load_order(db, order_id)
                if order is None or order.status in (
                    OrderStatus.CANCELLED, OrderStatus.FILLED, OrderStatus.REJECTED
                ):
                    return

                fills, remaining = depth_walk(book, order.side.value, remaining, FEE_RATE)
                if not fills:
                    continue

                base_cur, quote_cur = parse_currencies(symbol)
                for f in fills:
                    if order.side.value == "BUY":
                        await apply_buy_fill(db, order.user_id, base_cur, quote_cur,
                                             f.fill_price, f.fill_quantity, f.fee)
                    else:
                        await apply_sell_fill(db, order.user_id, base_cur, quote_cur,
                                              f.fill_price, f.fill_quantity, f.fee)

                await persist_fills(db, order, fills, remaining)
                await db.commit()
                await db.refresh(order)
                for fill_row in order.fills[-len(fills):]:
                    await publish_fill_event(redis_client, order, fill_row, order.status.value)

        if remaining > Decimal("0"):
            log.warning("market_handler watcher: gave up on order %s after %d iterations",
                        order_id, iteration)
    finally:
        mirror.unsubscribe_book(redis_sym, q)
