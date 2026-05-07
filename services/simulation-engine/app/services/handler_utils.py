"""
Shared helpers used by all order handlers.
"""
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import redis.asyncio as aioredis
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.order import ExecutionMode, Order, OrderFill, OrderStatus
from ..services.fill_engine import FillRecord


def symbol_to_redis_key(symbol: str) -> str:
    """Convert 'BTC/USDT' → 'BTCUSDT' for Redis key lookups."""
    return symbol.replace("/", "").upper()


def parse_currencies(symbol: str) -> tuple[str, str]:
    """
    Split 'BTC/USDT' → ('BTC', 'USDT').
    Falls back to splitting on the last 4 chars if no slash.
    """
    if "/" in symbol:
        parts = symbol.split("/", 1)
        return parts[0].upper(), parts[1].upper()
    # No slash — assume last 4 chars are the quote currency
    return symbol[:-4].upper(), symbol[-4:].upper()


async def persist_fills(
    db: AsyncSession,
    order: Order,
    fills: list[FillRecord],
    remaining_qty: Decimal,
) -> None:
    """
    Write OrderFill rows and update order status in one flush.
    Does NOT commit — caller must commit.
    """
    for f in fills:
        fill_row = OrderFill(
            order_id=order.id,
            fill_price=f.fill_price,
            fill_quantity=f.fill_quantity,
            fee=f.fee,
            fee_currency=f.fee_currency,
            execution_mode=ExecutionMode.SIMULATION,
            filled_at=datetime.now(timezone.utc),
        )
        db.add(fill_row)

    if remaining_qty <= Decimal("0"):
        order.status = OrderStatus.FILLED
    else:
        order.status = OrderStatus.PARTIALLY_FILLED

    order.updated_at = datetime.now(timezone.utc)
    await db.flush()


async def publish_fill_event(
    redis_client: aioredis.Redis,
    order: Order,
    fill: OrderFill | None,
    final_status: str,
) -> None:
    """
    Publish a fill event to the user's fills channel.
    Pass fill=None for status-only events (e.g. CANCELLED / REJECTED).
    """
    payload: dict = {
        "order_id": str(order.id),
        "user_id": str(order.user_id),
        "symbol": order.symbol,
        "side": order.side.value if hasattr(order.side, "value") else order.side,
        "order_status": final_status,
    }
    if fill is not None:
        payload.update(
            {
                "fill_id": str(fill.id),
                "fill_price": str(fill.fill_price),
                "fill_quantity": str(fill.fill_quantity),
                "fee": str(fill.fee),
                "fee_currency": fill.fee_currency,
                "filled_at": fill.filled_at.isoformat() if fill.filled_at else None,
            }
        )
    channel = f"fills.{order.user_id}"
    await redis_client.publish(channel, json.dumps(payload))


async def load_order(db: AsyncSession, order_id: uuid.UUID) -> Order | None:
    result = await db.execute(
        sa.select(Order).where(Order.id == order_id)
    )
    return result.scalar_one_or_none()
