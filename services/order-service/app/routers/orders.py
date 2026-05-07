import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies.auth import get_current_user_id
from ..models.order import ExecutionMode, Order, OrderStatus
from ..schemas.order import OrderResponse, PlaceOrderRequest, PlaceOrderResponse

router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.post("", response_model=PlaceOrderResponse, status_code=status.HTTP_201_CREATED)
async def place_order(
    body: PlaceOrderRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Submit a new order. The order is saved with status PENDING.
    The Simulation Engine (Sprint 5) will pick it up and fill it.
    """
    # Validate price requirement for LIMIT orders
    try:
        body.validate_price()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    order = Order(
        user_id=user_id,
        symbol=body.symbol.upper(),
        side=body.side,
        order_type=body.order_type,
        market_type=body.market_type,
        quantity=body.quantity,
        price=body.price,
        status=OrderStatus.PENDING,
        execution_mode=ExecutionMode.SIMULATION,  # Sprint 5 will derive from user's account mode
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

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
    """Cancel an open or pending order. Only the order owner can cancel."""
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

    order.status = OrderStatus.CANCELLED
    await db.commit()
