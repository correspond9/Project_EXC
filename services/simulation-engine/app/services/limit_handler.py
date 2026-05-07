"""
Limit order handler.

When a LIMIT order arrives:
  1. Mark the order OPEN and store it in the in-memory registry.
  2. Subscribe to order-book updates for the symbol.
  3. On each update, evaluate eligible fills (price ≤ ask for BUY, ≥ bid for SELL).
  4. Write fills to DB, update wallet, publish events.
  5. Remove from registry once FILLED.

Multiple limit orders for the same symbol share a single Redis Pub/Sub subscription.
"""
import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
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


@dataclass
class OpenLimitOrder:
    order_id: uuid.UUID
    user_id: uuid.UUID
    symbol: str              # "BTC/USDT"
    side: str                # "BUY" / "SELL"
    limit_price: Decimal
    remaining: Decimal
    locked_at_price: Decimal  # price used to compute locked balance


class LimitOrderHandler:
    """
    Singleton (one per process) that keeps all open limit orders in memory
    and evaluates them on every order-book update.
    """

    def __init__(self) -> None:
        # redis_sym → list of open orders
        self._orders: dict[str, list[OpenLimitOrder]] = {}
        # redis_sym → background task
        self._tasks: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    async def register(
        self,
        order_msg: dict,
        mirror: OrderBookMirror,
        redis_client,
    ) -> None:
        order_id = uuid.UUID(order_msg["order_id"])
        redis_sym = symbol_to_redis_key(order_msg["symbol"])
        limit_price = Decimal(str(order_msg["price"]))

        entry = OpenLimitOrder(
            order_id=order_id,
            user_id=uuid.UUID(order_msg["user_id"]),
            symbol=order_msg["symbol"],
            side=order_msg["side"],
            limit_price=limit_price,
            remaining=Decimal(str(order_msg["quantity"])),
            locked_at_price=limit_price,
        )

        # Mark order OPEN in DB
        async with AsyncSessionLocal() as db:
            order = await load_order(db, order_id)
            if order is None:
                return
            order.status = OrderStatus.OPEN
            order.updated_at = datetime.now(timezone.utc)
            await db.commit()

        async with self._lock:
            self._orders.setdefault(redis_sym, []).append(entry)
            if redis_sym not in self._tasks:
                self._tasks[redis_sym] = asyncio.create_task(
                    self._watch_symbol(redis_sym, mirror, redis_client)
                )

    async def _watch_symbol(
        self, redis_sym: str, mirror: OrderBookMirror, redis_client
    ) -> None:
        q = mirror.subscribe_book(redis_sym)
        log.info("limit_handler: watching %s", redis_sym)
        try:
            while True:
                try:
                    book = await asyncio.wait_for(q.get(), timeout=60.0)
                except asyncio.TimeoutError:
                    # Keep watching; orders might still be open
                    async with self._lock:
                        if not self._orders.get(redis_sym):
                            break
                    continue

                async with self._lock:
                    orders_for_sym = list(self._orders.get(redis_sym, []))

                if not orders_for_sym:
                    break

                for entry in orders_for_sym:
                    await self._try_fill(entry, book, redis_client)

                # Remove fully filled / cancelled entries
                async with self._lock:
                    self._orders[redis_sym] = [
                        o for o in self._orders.get(redis_sym, [])
                        if o.remaining > Decimal("0")
                    ]
                    if not self._orders[redis_sym]:
                        break

        finally:
            mirror.unsubscribe_book(redis_sym, q)
            async with self._lock:
                self._tasks.pop(redis_sym, None)
            log.info("limit_handler: stopped watching %s", redis_sym)

    async def _try_fill(
        self, entry: OpenLimitOrder, book: dict, redis_client
    ) -> None:
        fills, remaining = depth_walk(
            book, entry.side, entry.remaining, FEE_RATE, limit_price=entry.limit_price
        )
        if not fills:
            return

        async with AsyncSessionLocal() as db:
            order = await load_order(db, entry.order_id)
            if order is None or order.status in (
                OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED
            ):
                entry.remaining = Decimal("0")
                return

            base_cur, quote_cur = parse_currencies(entry.symbol)
            for f in fills:
                if entry.side == "BUY":
                    await apply_buy_fill(db, entry.user_id, base_cur, quote_cur,
                                         f.fill_price, f.fill_quantity, f.fee)
                else:
                    await apply_sell_fill(db, entry.user_id, base_cur, quote_cur,
                                          f.fill_price, f.fill_quantity, f.fee)

            await persist_fills(db, order, fills, remaining)
            await db.commit()
            await db.refresh(order)

            for fill_row in order.fills[-len(fills):]:
                await publish_fill_event(redis_client, order, fill_row, order.status.value)

            # Return over-reserved locked balance on full fill (limit fills at ≤ limit_price)
            if remaining <= Decimal("0") and entry.side == "BUY":
                total_cost = sum(f.fill_price * f.fill_quantity + f.fee for f in fills)
                locked = entry.locked_at_price * (entry.remaining - remaining + sum(f.fill_quantity for f in fills))
                over = locked - total_cost
                if over > Decimal("0"):
                    await release_locked_balance(db, entry.user_id, quote_cur, over)
                    await db.commit()

        entry.remaining = remaining
