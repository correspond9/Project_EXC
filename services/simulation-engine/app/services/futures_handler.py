"""
Futures order handler for the simulation engine.

Handles opening and closing leveraged LONG/SHORT positions.
On each market.ticker.* event, re-publishes updated unrealised P&L for all
open positions owned by affected users.
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import redis.asyncio as aioredis
import sqlalchemy as sa

from ..config import settings
from ..database import AsyncSessionLocal
from ..models.futures import (
    FuturesExecutionMode,
    MarginAccount,
    Position,
    PositionSide,
    PositionStatus,
)
from ..models.order import Order, OrderStatus
from ..services.order_book_mirror import OrderBookMirror

log = logging.getLogger(__name__)

FEE_RATE = Decimal(str(settings.SIM_FEE_RATE))
MAINT_MARGIN_RATE = Decimal("0.005")  # 0.5% maintenance margin


def _calc_liquidation_price(
    entry_price: Decimal, leverage: int, side: str
) -> Decimal:
    """
    Liquidation price formula:
      LONG:  entry * (1 - 1/leverage + maint_margin_rate)
      SHORT: entry * (1 + 1/leverage - maint_margin_rate)
    """
    lev = Decimal(str(leverage))
    if side == "LONG":
        return entry_price * (Decimal("1") - Decimal("1") / lev + MAINT_MARGIN_RATE)
    else:
        return entry_price * (Decimal("1") + Decimal("1") / lev - MAINT_MARGIN_RATE)


def _calc_unrealised_pnl(
    side: str, entry_price: Decimal, current_price: Decimal, quantity: Decimal
) -> Decimal:
    """
    LONG:  (current - entry) * qty
    SHORT: (entry - current) * qty
    """
    if side == "LONG":
        return (current_price - entry_price) * quantity
    else:
        return (entry_price - current_price) * quantity


async def handle_futures_order(
    order_msg: dict,
    mirror: OrderBookMirror,
    redis_client: aioredis.Redis,
) -> None:
    """
    Dispatch a futures order to open or close a position.
    Called from order_subscriber for FUTURES market_type orders.
    """
    reduce_only = order_msg.get("reduce_only", False)
    if reduce_only:
        await _close_position(order_msg, mirror, redis_client)
    else:
        await _open_position(order_msg, mirror, redis_client)


async def _open_position(
    order_msg: dict,
    mirror: OrderBookMirror,
    redis_client: aioredis.Redis,
) -> None:
    """Open a new futures position (LONG or SHORT)."""
    order_id = uuid.UUID(order_msg["order_id"])
    user_id = uuid.UUID(order_msg["user_id"])
    symbol = order_msg["symbol"]  # e.g. BTC/USDT
    side_str = order_msg["side"]  # BUY → LONG, SELL → SHORT
    quantity = Decimal(order_msg["quantity"])
    leverage = int(order_msg.get("leverage") or 1)
    redis_sym = symbol.replace("/", "").upper()

    # Determine position side
    pos_side = PositionSide.LONG if side_str == "BUY" else PositionSide.SHORT

    # Get entry price from book or from order price
    price_str = order_msg.get("price")
    if price_str:
        entry_price = Decimal(price_str)
    else:
        # Market order — use best ask/bid from mirror
        book = mirror.get_book(redis_sym)
        if book is None:
            log.warning("futures_handler: no book for %s — using ticker", redis_sym)
            raw = await redis_client.hget(f"ticker:{redis_sym}", "c")
            if raw is None:
                log.error("futures_handler: no price for %s — rejecting order %s", redis_sym, order_id)
                await _set_order_status(order_id, OrderStatus.REJECTED)
                return
            entry_price = Decimal(raw.decode() if isinstance(raw, bytes) else raw)
        else:
            levels = book.get("asks" if side_str == "BUY" else "bids", [])
            if not levels:
                log.error("futures_handler: empty book for %s", redis_sym)
                await _set_order_status(order_id, OrderStatus.REJECTED)
                return
            entry_price = Decimal(str(levels[0][0]))

    margin = (quantity * entry_price) / Decimal(str(leverage))
    fee = quantity * entry_price * FEE_RATE
    liquidation_price = _calc_liquidation_price(entry_price, leverage, pos_side.value)

    async with AsyncSessionLocal() as db:
        # Create position
        position = Position(
            user_id=user_id,
            order_id=order_id,
            symbol=symbol,
            side=pos_side,
            execution_mode=FuturesExecutionMode.SIMULATION,
            quantity=quantity,
            entry_price=entry_price,
            leverage=leverage,
            margin=margin,
            liquidation_price=liquidation_price,
            unrealised_pnl=Decimal("0"),
            status=PositionStatus.OPEN,
        )
        db.add(position)

        # Mark order FILLED
        result = await db.execute(sa.select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if order:
            order.status = OrderStatus.FILLED

        await db.commit()
        await db.refresh(position)

    # Publish position open event
    event = {
        "type": "position_opened",
        "user_id": str(user_id),
        "position_id": str(position.id),
        "symbol": symbol,
        "side": pos_side.value,
        "quantity": str(quantity),
        "entry_price": str(entry_price),
        "leverage": leverage,
        "margin": str(margin),
        "liquidation_price": str(liquidation_price),
        "fee": str(fee),
        "order_id": str(order_id),
    }
    await redis_client.publish(f"fills.{user_id}", json.dumps(event))
    log.info(
        "futures_handler: opened %s %s qty=%s lev=%sx entry=%s liq=%s",
        pos_side.value, symbol, quantity, leverage, entry_price, liquidation_price,
    )


async def _close_position(
    order_msg: dict,
    mirror: OrderBookMirror,
    redis_client: aioredis.Redis,
) -> None:
    """Close (reduce/fully close) an open futures position."""
    order_id = uuid.UUID(order_msg["order_id"])
    user_id = uuid.UUID(order_msg["user_id"])
    symbol = order_msg["symbol"]
    close_qty = Decimal(order_msg["quantity"])
    redis_sym = symbol.replace("/", "").upper()

    # Get close price
    price_str = order_msg.get("price")
    if price_str:
        close_price = Decimal(price_str)
    else:
        raw = await redis_client.hget(f"ticker:{redis_sym}", "c")
        if raw is None:
            log.error("futures_handler: no close price for %s", redis_sym)
            await _set_order_status(order_id, OrderStatus.REJECTED)
            return
        close_price = Decimal(raw.decode() if isinstance(raw, bytes) else raw)

    async with AsyncSessionLocal() as db:
        pos_result = await db.execute(
            sa.select(Position).where(
                Position.user_id == user_id,
                Position.symbol == symbol,
                Position.status == PositionStatus.OPEN,
                Position.execution_mode == FuturesExecutionMode.SIMULATION,
            )
        )
        position = pos_result.scalar_one_or_none()
        if position is None:
            log.warning("futures_handler: no open position for user %s symbol %s", user_id, symbol)
            await _set_order_status(order_id, OrderStatus.REJECTED)
            return

        side_str = position.side.value
        entry_price = Decimal(str(position.entry_price))
        qty = Decimal(str(position.quantity))
        leverage = int(position.leverage)

        # Calculate realised P&L on the closed portion
        pnl = _calc_unrealised_pnl(side_str, entry_price, close_price, close_qty)
        fee = close_qty * close_price * FEE_RATE
        net_pnl = pnl - fee
        margin_per_unit = Decimal(str(position.margin)) / qty
        margin_released = margin_per_unit * close_qty

        if close_qty >= qty:
            # Fully close
            position.status = PositionStatus.CLOSED
            position.realised_pnl = net_pnl
            position.closed_price = close_price
            position.closed_at = datetime.now(timezone.utc).isoformat()
            position.quantity = Decimal("0")
        else:
            # Partial close
            position.quantity = qty - close_qty
            position.margin = Decimal(str(position.margin)) - margin_released
            position.realised_pnl = (
                Decimal(str(position.realised_pnl or "0")) + net_pnl
            )

        # Return margin + P&L to margin account
        margin_acct_result = await db.execute(
            sa.select(MarginAccount).where(
                MarginAccount.user_id == user_id,
                MarginAccount.execution_mode == FuturesExecutionMode.SIMULATION,
            )
        )
        margin_account = margin_acct_result.scalar_one_or_none()
        if margin_account:
            margin_account.used_margin = max(
                Decimal("0"),
                Decimal(str(margin_account.used_margin)) - margin_released,
            )
            # Net P&L updates total balance and available margin
            margin_account.total_margin_balance = (
                Decimal(str(margin_account.total_margin_balance)) + net_pnl
            )
            margin_account.available_margin = (
                Decimal(str(margin_account.available_margin)) + margin_released + net_pnl
            )

        # Mark order FILLED
        result = await db.execute(sa.select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if order:
            order.status = OrderStatus.FILLED

        await db.commit()

    # Publish close event
    event = {
        "type": "position_closed",
        "user_id": str(user_id),
        "position_id": str(position.id),
        "symbol": symbol,
        "side": side_str,
        "quantity": str(close_qty),
        "close_price": str(close_price),
        "realised_pnl": str(net_pnl),
        "fee": str(fee),
        "order_id": str(order_id),
    }
    await redis_client.publish(f"fills.{user_id}", json.dumps(event))
    log.info(
        "futures_handler: closed %s %s qty=%s @ %s pnl=%s",
        side_str, symbol, close_qty, close_price, net_pnl,
    )


async def _set_order_status(order_id: uuid.UUID, new_status: OrderStatus) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(sa.select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if order:
            order.status = new_status
            await db.commit()


# ── Real-time position monitor ─────────────────────────────────────────────────

class PositionMonitor:
    """
    Subscribes to market.ticker.* Redis channel and pushes unrealised P&L
    updates for all open futures positions on each price tick.
    Also checks for liquidation triggers.
    """

    async def start(self, redis_client: aioredis.Redis) -> None:
        log.info("PositionMonitor: starting")
        while True:
            try:
                await self._run(redis_client)
            except asyncio.CancelledError:
                log.info("PositionMonitor: cancelled")
                return
            except Exception as exc:
                log.exception("PositionMonitor: error — %s — reconnecting in 5s", exc)
                await asyncio.sleep(5)

    async def _run(self, redis_client: aioredis.Redis) -> None:
        pubsub = redis_client.pubsub()
        await pubsub.psubscribe("market.ticker.*")
        log.info("PositionMonitor: subscribed to market.ticker.*")

        async for raw in pubsub.listen():
            if raw["type"] != "pmessage":
                continue
            try:
                channel = raw["channel"]
                if isinstance(channel, bytes):
                    channel = channel.decode()
                # channel = "market.ticker.BTCUSDT"
                redis_sym = channel.split(".")[-1].upper()  # BTCUSDT
                symbol_slash = redis_sym[:-4] + "/" + redis_sym[-4:]  # BTC/USDT

                data = json.loads(raw["data"])
                current_price = Decimal(str(data.get("c") or data.get("last_price") or "0"))
                if current_price <= Decimal("0"):
                    continue

                await self._process_symbol(redis_sym, symbol_slash, current_price, redis_client)
            except Exception as exc:
                log.debug("PositionMonitor: tick error — %s", exc)

    async def _process_symbol(
        self,
        redis_sym: str,
        symbol_slash: str,
        current_price: Decimal,
        redis_client: aioredis.Redis,
    ) -> None:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                sa.select(Position).where(
                    Position.symbol == symbol_slash,
                    Position.status == PositionStatus.OPEN,
                    Position.execution_mode == FuturesExecutionMode.SIMULATION,
                )
            )
            positions = result.scalars().all()

            for pos in positions:
                entry_price = Decimal(str(pos.entry_price))
                qty = Decimal(str(pos.quantity))
                side_str = pos.side.value

                new_upnl = _calc_unrealised_pnl(side_str, entry_price, current_price, qty)
                pos.unrealised_pnl = new_upnl

                # Check liquidation
                liq_price = Decimal(str(pos.liquidation_price))
                liquidated = (
                    (side_str == "LONG" and current_price <= liq_price)
                    or (side_str == "SHORT" and current_price >= liq_price)
                )
                if liquidated:
                    await self._liquidate(pos, current_price, db, redis_client)

                # Publish P&L update
                event = {
                    "type": "pnl_update",
                    "user_id": str(pos.user_id),
                    "position_id": str(pos.id),
                    "symbol": pos.symbol,
                    "side": side_str,
                    "unrealised_pnl": str(new_upnl),
                    "current_price": str(current_price),
                    "liquidation_price": str(liq_price),
                    "quantity": str(qty),
                    "entry_price": str(entry_price),
                    "leverage": pos.leverage,
                    "margin": str(pos.margin),
                }
                await redis_client.publish(
                    f"fills.{pos.user_id}", json.dumps(event)
                )

            await db.commit()

    async def _liquidate(
        self,
        pos: Position,
        current_price: Decimal,
        db,
        redis_client: aioredis.Redis,
    ) -> None:
        """Force-close a position that crossed the liquidation price."""
        qty = Decimal(str(pos.quantity))
        entry_price = Decimal(str(pos.entry_price))
        pnl = _calc_unrealised_pnl(pos.side.value, entry_price, current_price, qty)
        margin = Decimal(str(pos.margin))

        pos.status = PositionStatus.LIQUIDATED
        pos.realised_pnl = pnl
        pos.closed_price = current_price
        pos.closed_at = datetime.now(timezone.utc).isoformat()
        pos.quantity = Decimal("0")

        # Wipe margin
        margin_result = await db.execute(
            sa.select(MarginAccount).where(
                MarginAccount.user_id == pos.user_id,
                MarginAccount.execution_mode == FuturesExecutionMode.SIMULATION,
            )
        )
        margin_account = margin_result.scalar_one_or_none()
        if margin_account:
            margin_account.used_margin = max(
                Decimal("0"),
                Decimal(str(margin_account.used_margin)) - margin,
            )
            # Margin is lost on liquidation
            margin_account.total_margin_balance = max(
                Decimal("0"),
                Decimal(str(margin_account.total_margin_balance)) - margin,
            )

        event = {
            "type": "liquidation",
            "user_id": str(pos.user_id),
            "position_id": str(pos.id),
            "symbol": pos.symbol,
            "side": pos.side.value,
            "liquidation_price": str(current_price),
            "realised_pnl": str(pnl),
        }
        await redis_client.publish(f"fills.{pos.user_id}", json.dumps(event))
        log.warning(
            "futures_handler: LIQUIDATED %s %s @ %s pnl=%s",
            pos.side.value, pos.symbol, current_price, pnl,
        )
