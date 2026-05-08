import json
import uuid
from decimal import Decimal
from typing import Annotated, List, Optional

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies.auth import get_current_user_id
from ..models.futures import ExecutionMode as FuturesExecutionMode
from ..models.futures import MarginAccount, Position, PositionStatus, UserPositionLimit
from ..models.order import ExecutionMode, Order, OrderStatus
from ..models.wallet import SimulationWallet
from ..redis_client import get_redis_pool
from ..schemas.order import OrderResponse, PlaceOrderRequest, PlaceOrderResponse

router = APIRouter(prefix="/api/orders", tags=["Orders"])

# Taker fee rate — must match simulation-engine's SIM_FEE_RATE
_FEE_RATE = Decimal("0.001")
# Slippage buffer added to MARKET order reserve (1%)
_SLIPPAGE_BUFFER = Decimal("0.01")
# Maintenance margin rate for liquidation calculation
_MAINT_MARGIN_RATE = Decimal("0.005")


def _parse_currencies(symbol: str) -> tuple[str, str]:
    """'BTC/USDT' → ('BTC', 'USDT'). Falls back to last-4-chars if no slash."""
    if "/" in symbol:
        parts = symbol.split("/", 1)
        return parts[0].upper(), parts[1].upper()
    return symbol[:-4].upper(), symbol[-4:].upper()


async def _get_wallet(
    db: AsyncSession, user_id: uuid.UUID, currency: str
) -> SimulationWallet | None:
    result = await db.execute(
        sa.select(SimulationWallet).where(
            SimulationWallet.user_id == user_id,
            SimulationWallet.currency == currency,
        )
    )
    return result.scalar_one_or_none()


async def _get_or_create_margin_account(
    db: AsyncSession, user_id: uuid.UUID
) -> MarginAccount:
    result = await db.execute(
        sa.select(MarginAccount).where(
            MarginAccount.user_id == user_id,
            MarginAccount.execution_mode == FuturesExecutionMode.SIMULATION,
        )
    )
    account = result.scalar_one_or_none()
    if account is None:
        account = MarginAccount(
            user_id=user_id,
            execution_mode=FuturesExecutionMode.SIMULATION,
            total_margin_balance=Decimal("0"),
            available_margin=Decimal("0"),
            used_margin=Decimal("0"),
        )
        db.add(account)
        await db.flush()
    return account


async def _get_last_price(symbol_no_slash: str) -> Decimal | None:
    """Fetch the last trade price for a symbol from Redis ticker cache."""
    redis = get_redis_pool()
    # Try hash key first (market-data-service stores as hash ticker:{SYM} field "c")
    raw = await redis.hget(f"ticker:{symbol_no_slash.upper()}", "c")
    if raw is not None:
        try:
            return Decimal(raw.decode() if isinstance(raw, bytes) else raw)
        except Exception:
            pass
    # Fallback: plain JSON key
    raw2 = await redis.get(f"ticker:{symbol_no_slash.upper()}")
    if raw2 is None:
        return None
    try:
        data = json.loads(raw2)
        return Decimal(str(data.get("c") or data.get("last_price") or "0")) or None
    except Exception:
        return None


@router.post("", response_model=PlaceOrderResponse, status_code=status.HTTP_201_CREATED)
async def place_order(
    body: PlaceOrderRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Submit a simulation order (Spot or Futures).
    For SPOT: validates wallet balance, locks funds.
    For FUTURES: validates margin account, reserves margin.
    """
    try:
        body.validate_price()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    symbol_upper = body.symbol.upper()
    redis_sym = symbol_upper.replace("/", "")

    if body.market_type == MarketType.FUTURES:
        # ── FUTURES path ───────────────────────────────────────────────────────
        leverage = body.leverage or 1

        if body.reduce_only:
            # Closing an existing position — validate it exists
            pos_result = await db.execute(
                sa.select(Position).where(
                    Position.user_id == user_id,
                    Position.symbol == symbol_upper,
                    Position.status == PositionStatus.OPEN,
                    Position.execution_mode == FuturesExecutionMode.SIMULATION,
                )
            )
            position = pos_result.scalar_one_or_none()
            if position is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"No open {symbol_upper} futures position to close.",
                )
            close_qty = Decimal(str(body.quantity))
            if close_qty > Decimal(str(position.quantity)):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Close quantity {close_qty} exceeds open position size "
                        f"{position.quantity}."
                    ),
                )
        else:
            # Opening a new position — need margin
            last_price = await _get_last_price(redis_sym)
            if last_price is None or last_price <= Decimal("0"):
                raise HTTPException(
                    status_code=503,
                    detail="Market price unavailable. Please try again shortly.",
                )
            ref_price = Decimal(str(body.price)) if body.price else last_price
            margin_required = (Decimal(str(body.quantity)) * ref_price) / Decimal(str(leverage))

            margin_account = await _get_or_create_margin_account(db, user_id)
            available = Decimal(str(margin_account.available_margin))
            if available < margin_required:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Insufficient margin. Required: {margin_required:.4f} USDT, "
                        f"Available: {available:.4f} USDT"
                    ),
                )

            # ── Position size limit check ──────────────────────────────────────
            _DEFAULT_MAX_NOTIONAL = Decimal("50000")
            limit_result = await db.execute(
                sa.select(UserPositionLimit).where(
                    UserPositionLimit.user_id == user_id
                )
            )
            pos_limit_row = limit_result.scalar_one_or_none()
            max_notional = (
                Decimal(str(pos_limit_row.max_position_value_usdt))
                if pos_limit_row
                else _DEFAULT_MAX_NOTIONAL
            )
            # Sum existing open position notional values
            open_pos_result = await db.execute(
                sa.select(Position).where(
                    Position.user_id == user_id,
                    Position.status == PositionStatus.OPEN,
                    Position.execution_mode == FuturesExecutionMode.SIMULATION,
                )
            )
            open_positions = open_pos_result.scalars().all()
            existing_notional = sum(
                Decimal(str(p.quantity)) * Decimal(str(p.entry_price))
                for p in open_positions
            )
            new_notional = Decimal(str(body.quantity)) * ref_price
            if existing_notional + new_notional > max_notional:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Position size limit exceeded. Your maximum total open position "
                        f"value is {max_notional:,.2f} USDT. "
                        f"Current: {existing_notional:,.2f} USDT, "
                        f"New order: {new_notional:,.2f} USDT."
                    ),
                )

            # Reserve margin
            margin_account.available_margin = available - margin_required
            margin_account.used_margin = (
                Decimal(str(margin_account.used_margin)) + margin_required
            )

    else:
        # ── SPOT path ──────────────────────────────────────────────────────────
        base_cur, quote_cur = _parse_currencies(symbol_upper)

        if body.side == body.side.BUY:
            lock_currency = quote_cur
            if body.order_type.value in ("LIMIT", "TAKE_PROFIT"):
                lock_price = Decimal(str(body.price))
            elif body.order_type.value == "STOP_LOSS":
                lock_price = Decimal(str(body.stop_price))
            else:
                last_price = await _get_last_price(redis_sym)
                if last_price is None or last_price <= Decimal("0"):
                    raise HTTPException(
                        status_code=503,
                        detail="Market price unavailable. Please try again shortly.",
                    )
                lock_price = last_price * (Decimal("1") + _SLIPPAGE_BUFFER)

            lock_amount = (
                Decimal(str(body.quantity)) * lock_price * (Decimal("1") + _FEE_RATE)
            )
        else:
            lock_currency = base_cur
            lock_amount = Decimal(str(body.quantity))

        wallet = await _get_wallet(db, user_id, lock_currency)
        available = Decimal(str(wallet.balance)) if wallet else Decimal("0")
        if available < lock_amount:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Insufficient {lock_currency} balance. "
                    f"Required: {lock_amount:.8f}, Available: {available:.8f}"
                ),
            )

        wallet.balance = available - lock_amount
        wallet.locked_balance = Decimal(str(wallet.locked_balance)) + lock_amount

    # ── Persist order ──────────────────────────────────────────────────────────
    order = Order(
        user_id=user_id,
        symbol=symbol_upper,
        side=body.side,
        order_type=body.order_type,
        market_type=body.market_type,
        quantity=body.quantity,
        price=body.price,
        stop_price=body.stop_price,
        leverage=body.leverage,
        reduce_only=body.reduce_only,
        status=OrderStatus.PENDING,
        execution_mode=ExecutionMode.SIMULATION,
    )
    db.add(order)
    await db.flush()

    await db.commit()
    await db.refresh(order)

    # ── Publish to simulation engine ───────────────────────────────────────────
    msg = {
        "order_id": str(order.id),
        "user_id": str(user_id),
        "symbol": symbol_upper,
        "side": body.side.value,
        "order_type": body.order_type.value,
        "market_type": body.market_type.value,
        "quantity": str(body.quantity),
        "price": str(body.price) if body.price else None,
        "stop_price": str(body.stop_price) if body.stop_price else None,
        "leverage": body.leverage,
        "reduce_only": body.reduce_only,
        "execution_mode": "SIMULATION",
    }
    redis = get_redis_pool()
    await redis.publish("orders.simulation", json.dumps(msg))

    return PlaceOrderResponse(order_id=order.id, status=order.status)


@router.get("", response_model=List[OrderResponse])
async def list_orders(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: Optional[str] = Query(default=None, alias="status"),
    limit: int = Query(default=50, le=200),
):
    """Return the authenticated user's orders (open and recent)."""
    q = select(Order).where(Order.user_id == user_id)

    if status_filter:
        try:
            q = q.where(Order.status == OrderStatus(status_filter.upper()))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown status: {status_filter}")

    q = q.order_by(Order.created_at.desc()).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_order(
    order_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Cancel an open or pending order. Releases locked balance back to available."""
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == user_id)
    )
    order = result.scalar_one_or_none()

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status not in (OrderStatus.PENDING, OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel an order with status {order.status.value}",
        )

    # ── Release locked funds / margin ──────────────────────────────────────────
    if order.market_type and order.market_type.value == "FUTURES" and not order.reduce_only:
        leverage = order.leverage or 1
        ref_price = Decimal(str(order.price or "0"))
        if ref_price > 0:
            margin_to_release = (
                Decimal(str(order.quantity)) * ref_price / Decimal(str(leverage))
            )
            margin_account = await _get_or_create_margin_account(db, user_id)
            margin_account.used_margin = max(
                Decimal("0"),
                Decimal(str(margin_account.used_margin)) - margin_to_release,
            )
            margin_account.available_margin = (
                Decimal(str(margin_account.available_margin)) + margin_to_release
            )
    else:
        # SPOT: release locked wallet funds
        base_cur, quote_cur = _parse_currencies(order.symbol)
        release_currency = quote_cur if order.side.value == "BUY" else base_cur

        total_filled = (
            sum(Decimal(str(f.fill_quantity)) for f in order.fills)
            if order.fills
            else Decimal("0")
        )
        unfilled_qty = Decimal(str(order.quantity)) - total_filled

        if order.side.value == "BUY":
            ref_price = Decimal(str(order.price or order.stop_price or "0"))
            release_amount = (
                unfilled_qty * ref_price * (Decimal("1") + _FEE_RATE)
                if ref_price
                else Decimal("0")
            )
        else:
            release_amount = unfilled_qty

        if release_amount > Decimal("0"):
            wallet = await _get_wallet(db, user_id, release_currency)
            if wallet:
                release = min(release_amount, Decimal(str(wallet.locked_balance)))
                wallet.locked_balance = Decimal(str(wallet.locked_balance)) - release
                wallet.balance = Decimal(str(wallet.balance)) + release

    order.status = OrderStatus.CANCELLED
    await db.commit()


@router.get("/margin", tags=["Futures"])
async def get_margin_account(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Return the user's simulation futures margin account balance."""
    account = await _get_or_create_margin_account(db, user_id)
    await db.commit()
    total = float(account.total_margin_balance)
    return {
        "total_margin_balance": str(account.total_margin_balance),
        "available_margin": str(account.available_margin),
        "used_margin": str(account.used_margin),
        "margin_usage_pct": round(float(account.used_margin) / total * 100, 2) if total > 0 else 0.0,
    }

