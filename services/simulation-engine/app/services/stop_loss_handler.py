"""
Stop-Loss order handler.

When a STOP_LOSS order arrives:
  1. Mark the order OPEN and register it.
  2. Subscribe to ticker updates for the symbol.
  3. On each ticker update, check if the last price crosses the stop_price:
       BUY  stop-loss: triggered when last_price >= stop_price
       SELL stop-loss: triggered when last_price <= stop_price
  4. When triggered, hand off to the market_handler for immediate execution.
"""
import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from ..config import settings
from ..database import AsyncSessionLocal
from ..models.order import OrderStatus
from ..services.handler_utils import load_order, symbol_to_redis_key
from ..services.market_handler import handle_market_order
from ..services.order_book_mirror import OrderBookMirror

log = logging.getLogger(__name__)


@dataclass
class OpenStopOrder:
    order_id: uuid.UUID
    user_id: uuid.UUID
    symbol: str      # "BTC/USDT"
    side: str        # "BUY" / "SELL"
    stop_price: Decimal
    quantity: Decimal


class StopLossHandler:
    def __init__(self) -> None:
        self._orders: dict[str, list[OpenStopOrder]] = {}
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
        raw_stop = order_msg.get("stop_price") or order_msg.get("price")
        if raw_stop is None:
            log.error("stop_loss_handler: no stop_price for order %s — rejecting", order_id)
            async with AsyncSessionLocal() as db:
                order = await load_order(db, order_id)
                if order:
                    order.status = OrderStatus.REJECTED
                    order.updated_at = datetime.now(timezone.utc)
                    await db.commit()
            return

        stop_price = Decimal(str(raw_stop))

        entry = OpenStopOrder(
            order_id=order_id,
            user_id=uuid.UUID(order_msg["user_id"]),
            symbol=order_msg["symbol"],
            side=order_msg["side"],
            stop_price=stop_price,
            quantity=Decimal(str(order_msg["quantity"])),
        )

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
        q = mirror.subscribe_ticker(redis_sym)
        log.info("stop_loss_handler: watching %s", redis_sym)
        try:
            while True:
                try:
                    ticker = await asyncio.wait_for(q.get(), timeout=60.0)
                except asyncio.TimeoutError:
                    async with self._lock:
                        if not self._orders.get(redis_sym):
                            break
                    continue

                last_price_raw = ticker.get("c") or ticker.get("last_price")
                if last_price_raw is None:
                    continue
                last_price = Decimal(str(last_price_raw))

                triggered: list[OpenStopOrder] = []
                async with self._lock:
                    remaining: list[OpenStopOrder] = []
                    for entry in self._orders.get(redis_sym, []):
                        if self._is_triggered(entry, last_price):
                            triggered.append(entry)
                        else:
                            remaining.append(entry)
                    self._orders[redis_sym] = remaining
                    if not remaining:
                        break

                for entry in triggered:
                    log.info(
                        "stop_loss_handler: triggering order %s at price %s",
                        entry.order_id, last_price,
                    )
                    market_msg = {
                        "order_id": str(entry.order_id),
                        "user_id": str(entry.user_id),
                        "symbol": entry.symbol,
                        "side": entry.side,
                        "order_type": "MARKET",
                        "quantity": str(entry.quantity),
                        "price": None,
                        "stop_price": None,
                        "execution_mode": "SIMULATION",
                    }
                    asyncio.create_task(
                        handle_market_order(market_msg, mirror, redis_client)
                    )
        finally:
            mirror.unsubscribe_ticker(redis_sym, q)
            async with self._lock:
                self._tasks.pop(redis_sym, None)
            log.info("stop_loss_handler: stopped watching %s", redis_sym)

    @staticmethod
    def _is_triggered(entry: OpenStopOrder, last_price: Decimal) -> bool:
        if entry.side == "SELL":
            return last_price <= entry.stop_price
        # BUY stop-loss (used to cap losses on a short, or for breakout buying)
        return last_price >= entry.stop_price
