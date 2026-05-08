"""
fill_listener.py
~~~~~~~~~~~~~~~~
Subscribes to Redis pattern ``fills.*`` and updates portfolio_holdings on
every fill event published by the simulation-engine.

Fill event format (published on channel fills.{user_id}):
{
    "order_id": "...",
    "user_id":  "...",
    "symbol":   "BTC/USDT",
    "side":     "BUY" | "SELL",
    "fill_price":    "...",
    "fill_quantity": "...",
    "fee":           "...",
    "fee_currency":  "USDT",
    "order_status":  "FILLED" | "PARTIALLY_FILLED",
    "fill_id":       "...",
    "filled_at":     "..."
}
"""
import asyncio
import json
import logging
import uuid
from decimal import Decimal, InvalidOperation

from sqlalchemy import select, text

from ..database import AsyncSessionLocal
from ..models.portfolio import PortfolioHolding
from ..redis_client import get_redis_pool

log = logging.getLogger(__name__)

_EXECUTION_MODE = "SIMULATION"


def _parse_symbol(symbol: str) -> tuple[str, str]:
    """'BTC/USDT' → ('BTC', 'USDT')"""
    parts = symbol.split("/")
    if len(parts) == 2:
        return parts[0].upper(), parts[1].upper()
    # fallback: assume last 4 chars are quote
    return symbol[:-4].upper(), symbol[-4:].upper()


async def _handle_fill(event: dict) -> None:
    """Process a single fill event and update portfolio_holdings."""
    try:
        user_id = uuid.UUID(event["user_id"])
        symbol: str = event["symbol"]
        side: str = event["side"].upper()
        fill_price = Decimal(str(event["fill_price"]))
        fill_qty = Decimal(str(event["fill_quantity"]))
        fee = Decimal(str(event.get("fee", "0")))
    except (KeyError, ValueError, InvalidOperation) as exc:
        log.warning("fill_listener: malformed event — %s | event: %s", exc, event)
        return

    base_asset, _quote = _parse_symbol(symbol)

    async with AsyncSessionLocal() as session:
        # Fetch or create holding
        result = await session.execute(
            select(PortfolioHolding).where(
                PortfolioHolding.user_id == user_id,
                PortfolioHolding.asset == base_asset,
                PortfolioHolding.execution_mode == _EXECUTION_MODE,
            )
        )
        holding: PortfolioHolding | None = result.scalar_one_or_none()

        if side == "BUY":
            if holding is None:
                holding = PortfolioHolding(
                    user_id=user_id,
                    asset=base_asset,
                    execution_mode=_EXECUTION_MODE,
                    quantity=Decimal("0"),
                    average_entry_price=Decimal("0"),
                    total_realised_pnl=Decimal("0"),
                )
                session.add(holding)

            # Weighted-average entry price
            old_qty = Decimal(str(holding.quantity))
            old_avg = Decimal(str(holding.average_entry_price))
            new_qty = old_qty + fill_qty
            if new_qty > 0:
                new_avg = (old_qty * old_avg + fill_qty * fill_price) / new_qty
            else:
                new_avg = fill_price

            holding.quantity = new_qty
            holding.average_entry_price = new_avg
            await session.execute(
                text("UPDATE portfolio_holdings SET updated_at = now() "
                     "WHERE id = :id"),
                {"id": holding.id},
            )

        elif side == "SELL":
            if holding is None:
                log.warning(
                    "fill_listener: SELL fill for unknown holding user=%s asset=%s",
                    user_id, base_asset,
                )
                return

            avg_entry = Decimal(str(holding.average_entry_price))
            realised = (fill_price - avg_entry) * fill_qty - fee
            new_qty = Decimal(str(holding.quantity)) - fill_qty
            if new_qty < 0:
                new_qty = Decimal("0")

            holding.quantity = new_qty
            holding.total_realised_pnl = Decimal(str(holding.total_realised_pnl)) + realised
            await session.execute(
                text("UPDATE portfolio_holdings SET updated_at = now() "
                     "WHERE id = :id"),
                {"id": holding.id},
            )

        await session.commit()


async def run_fill_listener() -> None:
    """
    Long-running coroutine.  Subscribes to Redis pattern ``fills.*``
    and dispatches each pmessage to _handle_fill().
    Automatically reconnects on transient errors.
    """
    while True:
        try:
            redis = get_redis_pool()
            pubsub = redis.pubsub()
            await pubsub.psubscribe("fills.*")
            log.info("fill_listener: subscribed to fills.*")
            async for message in pubsub.listen():
                if message["type"] != "pmessage":
                    continue
                try:
                    raw = message["data"]
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8")
                    event = json.loads(raw)
                    await _handle_fill(event)
                except Exception as exc:  # noqa: BLE001
                    log.error("fill_listener: error processing message — %s", exc)
        except asyncio.CancelledError:
            log.info("fill_listener: cancelled, shutting down")
            return
        except Exception as exc:  # noqa: BLE001
            log.error("fill_listener: connection error — %s; retrying in 5s", exc)
            await asyncio.sleep(5)
