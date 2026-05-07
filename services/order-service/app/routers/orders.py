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
from ..models.order import ExecutionMode, Order, OrderStatus
from ..models.wallet import SimulationWallet
from ..redis_client import get_redis_pool
from ..schemas.order import OrderResponse, PlaceOrderRequest, PlaceOrderResponse

router = APIRouter(prefix="/api/orders", tags=["Orders"])

# Taker fee rate — must match simulation-engine's SIM_FEE_RATE
_FEE_RATE = Decimal("0.001")
# Slippage buffer added to MARKET order reserve (1%)
_SLIPPAGE_BUFFER = Decimal("0.01")


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


async def _get_last_price(symbol_no_slash: str) -> Decimal | None:
    """Fetch the last trade price for a symbol from Redis ticker cache."""
    redis = get_redis_pool()
    raw = await redis.get(f"ticker:{symbol_no_slash.upper()}")
    if raw is None:
        return None
    try:
        data = json.loads(raw)
        # Binance mini-ticker: 'c' = last price
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
    Submit a simulation order.
    Validates wallet balance, locks funds, saves the order as PENDING,
    then publishes to Redis `orders.simulation` for the simulation engine.
    """
    try:
        body.validate_price()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    symbol_upper = body.symbol.upper()
    base_cur, quote_cur = _parse_currencies(symbol_upper)
    # Redis key uses no-slash format
    redis_sym = symbol_upper.replace("/", "")

    # ── Determine lock amount ──────────────────────────────────────────────────
    if body.side == body.side.BUY:
        # BUY: lock quote currency (USDT)
        lock_currency = quote_cur
        if body.order_type.value in ("LIMIT", "TAKE_PROFIT"):
            lock_price = Decimal(str(body.price))
        elif body.order_type.value in ("STOP_LOSS",):
            lock_price = Decimal(str(body.stop_price))
        else:
            # MARKET: fetch current ask price estimate
            last_price = await _get_last_price(redis_sym)
            if last_price is None or last_price <= Decimal("0"):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Market price unavailable. Please try again shortly.",
                )
            lock_price = last_price * (Decimal("1") + _SLIPPAGE_BUFFER)

        lock_amount = Decimal(str(body.quantity)) * lock_price * (Decimal("1") + _FEE_RATE)
    else:
        # SELL: lock base currency (e.g. BTC)
        lock_currency = base_cur
        lock_amount = Decimal(str(body.quantity))

    # ── Check balance ──────────────────────────────────────────────────────────
    wallet = await _get_wallet(db, user_id, lock_currency)
    available = Decimal(str(wallet.balance)) if wallet else Decimal("0")
    if available < lock_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Insufficient {lock_currency} balance. "
                f"Required: {lock_amount:.8f}, Available: {available:.8f}"
            ),
        )

    # ── Lock funds ─────────────────────────────────────────────────────────────
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
        status=OrderStatus.PENDING,
        execution_mode=ExecutionMode.SIMULATION,
    )
    db.add(order)
    await db.flush()   # get order.id before commit

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
        "execution_mode": "SIMULATION",
    }
    redis = get_redis_pool()
    await redis.publish("orders.simulation", json.dumps(msg))

    return PlaceOrderResponse(
        order_id=order.id,
        status=order.status,
        message="Order received and queued for execution.",
    )


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

    # ── Release locked funds ───────────────────────────────────────────────────
    base_cur, quote_cur = _parse_currencies(order.symbol)
    if order.side.value == "BUY":
        release_currency = quote_cur
    else:
        release_currency = base_cur

    # Estimate remaining locked amount (full lock for PENDING / OPEN, proportional for PARTIAL)
    total_filled = sum(
        Decimal(str(f.fill_quantity)) for f in order.fills
    ) if order.fills else Decimal("0")
    unfilled_qty = Decimal(str(order.quantity)) - total_filled

    if order.side.value == "BUY":
        # Use the order price; for MARKET orders, we may not have an exact price stored.
        # Fall back to a best-effort: release what's in locked_balance for this order.
        # The safest approach is to release proportionally.
        ref_price = Decimal(str(order.price or order.stop_price or "0"))
        release_amount = unfilled_qty * ref_price * (Decimal("1") + _FEE_RATE) if ref_price else Decimal("0")
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

