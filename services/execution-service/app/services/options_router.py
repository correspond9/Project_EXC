"""
Sprint 22 — Options order router.

Subscribes to 'orders.live.options' Redis channel, routes orders to Deribit
via the DeribitClient CCXT wrapper, polls for fills, records results, and
publishes fill events back to 'fills.{user_id}'.

Message payload schema (published by order-service):
{
  "order_id": "<uuid>",
  "user_id": "<uuid>",
  "symbol": "<Deribit instrument name, e.g. BTC-27DEC24-100000-C>",
  "side": "buy" | "sell",
  "order_type": "limit" | "market",
  "quantity": "1.0",
  "price": "0.05",          // null for market
  "execution_mode": "LIVE"
}
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from decimal import Decimal

from sqlalchemy import select, text

from ..config import settings
from ..database import AsyncSessionLocal
from ..models.order import ExecutionMode, Order, OrderFill, OrderStatus
from ..redis_client import get_redis_pool
from .deribit_client import DeribitClient

logger = logging.getLogger(__name__)

# Poll timeout: 30 minutes
_POLL_TIMEOUT = 1800
_POLL_INTERVAL = 5


class OptionsOrderRouter:
    """Subscribes to orders.live.options and routes to Deribit."""

    def __init__(self, client: DeribitClient) -> None:
        self._client = client

    async def run(self) -> None:
        """Subscribe to orders.live.options and process indefinitely."""
        redis = get_redis_pool()
        pubsub = redis.pubsub()
        await pubsub.subscribe("orders.live.options")
        logger.info("OptionsOrderRouter: subscribed to orders.live.options")
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            try:
                data = json.loads(message["data"])
                asyncio.create_task(self._handle(data))
            except Exception as exc:
                logger.exception("Error dispatching options order: %s", exc)

    async def _handle(self, data: dict) -> None:
        order_id = uuid.UUID(data["order_id"])
        user_id = uuid.UUID(data["user_id"])
        instrument = data["symbol"]  # Full Deribit instrument name
        side = data["side"]
        order_type = data.get("order_type", "limit")
        quantity = float(data["quantity"])
        price = float(data["price"]) if data.get("price") else None

        logger.info(
            "OptionsOrderRouter: handling order %s — %s %s %s qty=%s",
            order_id,
            side,
            instrument,
            order_type,
            quantity,
        )

        async with AsyncSessionLocal() as db:
            try:
                # Mark order as OPEN
                result = await db.execute(select(Order).where(Order.id == order_id))
                order = result.scalar_one_or_none()
                if order is None:
                    logger.error("Order %s not found in DB", order_id)
                    return

                # Place on Deribit
                ext_order = await self._client.place_option(
                    instrument=instrument,
                    side=side,
                    amount=quantity,
                    price=price,
                    order_type=order_type,
                )
                ext_id = str(ext_order.get("id", ""))
                order.external_order_id = ext_id
                order.status = OrderStatus.OPEN
                await db.commit()

                # Poll until filled or timeout
                fill_price, fill_qty = await self._poll_until_filled(ext_id, instrument)

                if fill_price is None:
                    order.status = OrderStatus.CANCELLED
                    await db.commit()
                    logger.warning("Options order %s timed out / cancelled", order_id)
                    return

                # Record fill
                fill = OrderFill(
                    order_id=order_id,
                    user_id=user_id,
                    symbol=instrument,
                    side=side,
                    fill_price=Decimal(str(fill_price)),
                    quantity=Decimal(str(fill_qty)),
                    fee=Decimal(str(fill_price * fill_qty * 0.0003)),  # Deribit maker fee ~0.03%
                    execution_mode=ExecutionMode.LIVE,
                )
                db.add(fill)
                order.status = OrderStatus.FILLED
                await db.commit()

                # Publish fill event
                redis = get_redis_pool()
                await redis.publish(
                    f"fills.{user_id}",
                    json.dumps(
                        {
                            "order_id": str(order_id),
                            "symbol": instrument,
                            "side": side,
                            "fill_price": str(fill_price),
                            "quantity": str(fill_qty),
                            "market_type": "OPTIONS",
                            "execution_mode": "LIVE",
                        }
                    ),
                )
                logger.info("Options order %s filled at %s", order_id, fill_price)

            except Exception as exc:
                logger.exception("Error processing options order %s: %s", order_id, exc)
                try:
                    result = await db.execute(select(Order).where(Order.id == order_id))
                    order = result.scalar_one_or_none()
                    if order:
                        order.status = OrderStatus.REJECTED
                        await db.commit()
                except Exception:
                    pass

    async def _poll_until_filled(
        self, ext_id: str, instrument: str
    ) -> tuple[float | None, float | None]:
        """Poll Deribit until the order is filled or timeout reached."""
        elapsed = 0
        while elapsed < _POLL_TIMEOUT:
            await asyncio.sleep(_POLL_INTERVAL)
            elapsed += _POLL_INTERVAL
            try:
                ext_order = await self._client.fetch_order(ext_id, instrument)
                deribit_status = ext_order.get("status", "")
                if deribit_status == "closed":
                    avg_price = ext_order.get("average") or ext_order.get("price")
                    filled_qty = ext_order.get("filled")
                    return float(avg_price or 0), float(filled_qty or 0)
                if deribit_status in ("canceled", "rejected", "expired"):
                    return None, None
            except Exception as exc:
                logger.warning("Poll error for options order %s: %s", ext_id, exc)

        logger.warning("Options order %s timed out after %ss", ext_id, _POLL_TIMEOUT)
        return None, None
