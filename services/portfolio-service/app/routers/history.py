"""
history.py — Trade history endpoints (reads from orders + order_fills tables)

Routes:
  GET /api/orders/history   — filled/partially-filled orders for the user
  GET /api/orders/fills     — fill records for a specific order
"""
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..models.order import OrderFillReadOnly, OrderReadOnly

router = APIRouter()
_bearer = HTTPBearer()


def _verify_token(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> uuid.UUID:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return uuid.UUID(user_id)
    except (JWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc


@router.get("/api/orders/history")
async def get_order_history(
    symbol: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    user_id: uuid.UUID = Depends(_verify_token),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return the user's filled / partially-filled orders with fill details."""
    stmt = (
        select(OrderReadOnly)
        .where(
            OrderReadOnly.user_id == user_id,
            OrderReadOnly.status.in_(["FILLED", "PARTIALLY_FILLED"]),
        )
        .order_by(OrderReadOnly.updated_at.desc())
        .limit(limit)
    )
    if symbol:
        stmt = stmt.where(OrderReadOnly.symbol == symbol)

    result = await db.execute(stmt)
    orders = result.scalars().all()

    out = []
    for o in orders:
        fills = [
            {
                "fill_id": str(f.id),
                "fill_price": str(f.fill_price),
                "fill_quantity": str(f.fill_quantity),
                "fee": str(f.fee),
                "fee_currency": f.fee_currency,
                "filled_at": f.filled_at.isoformat() if f.filled_at else None,
            }
            for f in o.fills
        ]
        # P&L: only computable for SELL orders with fills
        realised_pnl = None
        out.append(
            {
                "order_id": str(o.id),
                "symbol": o.symbol,
                "side": o.side,
                "order_type": o.order_type,
                "quantity": str(o.quantity),
                "price": str(o.price) if o.price else None,
                "status": o.status,
                "execution_mode": o.execution_mode,
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "updated_at": o.updated_at.isoformat() if o.updated_at else None,
                "fills": fills,
            }
        )
    return out


@router.get("/api/orders/fills")
async def get_order_fills(
    order_id: uuid.UUID = Query(...),
    user_id: uuid.UUID = Depends(_verify_token),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return all fill records for a specific order (must belong to the requesting user)."""
    # Verify ownership
    order_result = await db.execute(
        select(OrderReadOnly).where(
            OrderReadOnly.id == order_id,
            OrderReadOnly.user_id == user_id,
        )
    )
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    fills_result = await db.execute(
        select(OrderFillReadOnly)
        .where(OrderFillReadOnly.order_id == order_id)
        .order_by(OrderFillReadOnly.filled_at.asc())
    )
    fills = fills_result.scalars().all()
    return [
        {
            "fill_id": str(f.id),
            "fill_price": str(f.fill_price),
            "fill_quantity": str(f.fill_quantity),
            "fee": str(f.fee),
            "fee_currency": f.fee_currency,
            "filled_at": f.filled_at.isoformat() if f.filled_at else None,
        }
        for f in fills
    ]
