"""Core live order router.

Subscribes to 'orders.live' Redis channel, routes orders to Binance via CCXT,
polls for fills, records results in the shared DB, and publishes fill events.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import ccxt.async_support as ccxt
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import AsyncSessionLocal
from ..models.order import ExecutionMode, MarketType, Order, OrderFill, OrderStatus
from ..redis_client import get_redis_pool
from .balance_sync import sync_futures_balances, sync_spot_balances
from .binance_client import BinanceClient

logger = logging.getLogger(__name__)

# Default fee rate — overridden by fee_configs table if present
_DEFAULT_FEE_RATE = Decimal("0.001")


class LiveOrderRouter:
    def __init__(self, client: BinanceClient) -> None:
        self._client = client

    async def run(self) -> None:
        """Subscribe to orders.live and process indefinitely."""
        redis = get_redis_pool()
        pubsub = redis.pubsub()
        await pubsub.subscribe("orders.live")
        logger.info("LiveOrderRouter: subscribed to orders.live")
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            try:
                data = json.loads(message["data"])
                asyncio.create_task(self._handle(data))
            except Exception as exc:
                logger.exception("Error dispatching live order: %s", exc)

    async def _handle(self, data: dict) -> None:
        order_id = uuid.UUID(data["order_id"])
        user_id = uuid.UUID(data["user_id"])
        symbol = data["symbol"]
        side = data["side"]
        order_type = data["order_type"]
        market_type = data.get("market_type", "SPOT")
        quantity = Decimal(data["quantity"])
        price = Decimal(data["price"]) if data.get("price") else None
        leverage = int(data.get("leverage") or 1)
        reduce_only = bool(data.get("reduce_only", False))

        logger.info("Processing LIVE order %s %s %s %s", order_id, symbol, side, quantity)

        try:
            if market_type == MarketType.FUTURES.value:
                ccxt_order = await self._client.place_futures_order(
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    quantity=quantity,
                    price=price,
                    leverage=leverage,
                    reduce_only=reduce_only,
                )
            else:
                ccxt_order = await self._client.place_spot_order(
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    quantity=quantity,
                    price=price,
                )
        except ccxt.InsufficientFunds as exc:
            logger.warning("Insufficient funds for order %s: %s", order_id, exc)
            await self._reject_order(order_id)
            return
        except ccxt.BaseError as exc:
            logger.error("CCXT error for order %s: %s", order_id, exc)
            await self._reject_order(order_id)
            return

        external_id = str(ccxt_order["id"])
        await self._store_external_id(order_id, external_id)

        # Poll for fill
        await self._poll_until_filled(
            order_id=order_id,
            user_id=user_id,
            external_id=external_id,
            symbol=symbol,
            market_type=market_type,
        )

    async def _poll_until_filled(
        self,
        order_id: uuid.UUID,
        user_id: uuid.UUID,
        external_id: str,
        symbol: str,
        market_type: str,
    ) -> None:
        deadline = asyncio.get_event_loop().time() + settings.ORDER_POLL_TIMEOUT_SECONDS
        while asyncio.get_event_loop().time() < deadline:
            await asyncio.sleep(settings.ORDER_POLL_INTERVAL_SECONDS)
            try:
                if market_type == MarketType.FUTURES.value:
                    raw = await self._client.fetch_futures_order(external_id, symbol)
                else:
                    raw = await self._client.fetch_spot_order(external_id, symbol)
            except Exception as exc:
                logger.warning("Poll error for order %s: %s", order_id, exc)
                continue

            binance_status = raw.get("status", "")
            if binance_status in ("closed", "filled"):
                await self._record_fill(order_id, user_id, raw, symbol, market_type)
                return
            elif binance_status in ("canceled", "rejected", "expired"):
                await self._reject_order(order_id)
                return

        # Timed out — mark as OPEN (partially or fully pending on exchange)
        logger.warning("Order %s timed out waiting for fill — left as OPEN", order_id)
        await self._set_order_status(order_id, OrderStatus.OPEN)

    async def _record_fill(
        self,
        order_id: uuid.UUID,
        user_id: uuid.UUID,
        raw: dict,
        symbol: str,
        market_type: str,
    ) -> None:
        fill_price = Decimal(str(raw.get("average") or raw.get("price") or 0))
        fill_qty = Decimal(str(raw.get("filled") or raw.get("amount") or 0))
        fee_info = raw.get("fee") or {}
        fee_amount = Decimal(str(fee_info.get("cost") or 0))
        fee_currency = str(fee_info.get("currency") or "USDT").upper()

        if fill_price <= 0 or fill_qty <= 0:
            logger.warning("Order %s fill has zero price/qty — skipping", order_id)
            return

        fee_rate = await self._get_fee_rate()
        if fee_amount == 0:
            fill_value = fill_price * fill_qty
            fee_amount = fill_value * fee_rate

        async with AsyncSessionLocal() as db:
            # Update order status
            order = await db.get(Order, order_id)
            if order:
                order.status = OrderStatus.FILLED

            # Write fill record
            fill = OrderFill(
                order_id=order_id,
                fill_price=fill_price,
                fill_quantity=fill_qty,
                fee=fee_amount,
                fee_currency=fee_currency,
                execution_mode=ExecutionMode.LIVE,
                filled_at=datetime.now(tz=timezone.utc),
            )
            db.add(fill)

            # Write fee_ledger entry (Sprint 18)
            fill_value = fill_price * fill_qty
            await db.execute(
                text(
                    "INSERT INTO fee_ledger "
                    "(id, user_id, order_id, fill_id, currency, fee_amount, fee_rate, "
                    " fill_value, fill_quantity, fill_price) "
                    "VALUES (gen_random_uuid(), :uid, :oid, :fid, :cur, :fee, :rate, "
                    "        :fval, :fqty, :fprice)"
                ),
                {
                    "uid": str(user_id),
                    "oid": str(order_id),
                    "fid": None,  # filled after flush
                    "cur": fee_currency,
                    "fee": float(fee_amount),
                    "rate": float(fee_rate),
                    "fval": float(fill_value),
                    "fqty": float(fill_qty),
                    "fprice": float(fill_price),
                },
            )

            await db.commit()

            # Sync balances from Binance
            if market_type == MarketType.FUTURES.value:
                await sync_futures_balances(db, user_id, self._client)
            else:
                await sync_spot_balances(db, user_id, self._client)

        # Publish fill event
        fill_event = {
            "order_id": str(order_id),
            "user_id": str(user_id),
            "symbol": symbol,
            "fill_price": str(fill_price),
            "fill_quantity": str(fill_qty),
            "fee": str(fee_amount),
            "fee_currency": fee_currency,
            "execution_mode": "LIVE",
        }
        redis = get_redis_pool()
        await redis.publish(f"fills.{user_id}", json.dumps(fill_event))
        logger.info("Fill recorded and published for order %s", order_id)

    async def _store_external_id(self, order_id: uuid.UUID, external_id: str) -> None:
        async with AsyncSessionLocal() as db:
            order = await db.get(Order, order_id)
            if order:
                order.external_order_id = external_id
                order.status = OrderStatus.OPEN
                await db.commit()

    async def _reject_order(self, order_id: uuid.UUID) -> None:
        await self._set_order_status(order_id, OrderStatus.REJECTED)

    async def _set_order_status(self, order_id: uuid.UUID, status: OrderStatus) -> None:
        async with AsyncSessionLocal() as db:
            order = await db.get(Order, order_id)
            if order:
                order.status = status
                await db.commit()

    async def _get_fee_rate(self) -> Decimal:
        try:
            async with AsyncSessionLocal() as db:
                row = await db.execute(
                    text("SELECT taker_fee FROM fee_configs WHERE is_active = true LIMIT 1")
                )
                result = row.fetchone()
                if result:
                    return Decimal(str(result[0]))
        except Exception:
            pass
        return _DEFAULT_FEE_RATE
