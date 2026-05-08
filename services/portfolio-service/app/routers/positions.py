"""
positions.py — Futures positions REST endpoint.

Routes:
  GET /api/positions          — open (and recent closed) positions for the current user
  GET /api/positions/margin   — margin account summary
"""
import uuid
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..models.futures import FuturesExecutionMode, MarginAccount, Position, PositionStatus

router = APIRouter()
_bearer = HTTPBearer()


def _verify_token(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> uuid.UUID:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError) as exc:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


def _fmt(val) -> str | None:
    if val is None:
        return None
    return str(Decimal(str(val)).normalize())


@router.get("/api/positions")
async def list_positions(
    status_filter: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(_verify_token),
) -> list[dict[str, Any]]:
    """Return futures positions for the authenticated user."""
    conditions = [
        Position.user_id == user_id,
        Position.execution_mode == FuturesExecutionMode.SIMULATION,
    ]
    if status_filter:
        try:
            conditions.append(Position.status == PositionStatus(status_filter.upper()))
        except ValueError:
            pass

    result = await db.execute(
        select(Position)
        .where(*conditions)
        .order_by(Position.created_at.desc())
    )
    positions = result.scalars().all()

    return [
        {
            "id": str(pos.id),
            "symbol": pos.symbol,
            "side": pos.side.value,
            "quantity": _fmt(pos.quantity),
            "entry_price": _fmt(pos.entry_price),
            "leverage": pos.leverage,
            "margin": _fmt(pos.margin),
            "liquidation_price": _fmt(pos.liquidation_price),
            "unrealised_pnl": _fmt(pos.unrealised_pnl),
            "realised_pnl": _fmt(pos.realised_pnl),
            "status": pos.status.value,
            "created_at": str(pos.created_at),
            "closed_at": str(pos.closed_at) if pos.closed_at else None,
        }
        for pos in positions
    ]


@router.get("/api/positions/margin")
async def get_margin_account(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(_verify_token),
) -> dict[str, Any]:
    """Return SIMULATION margin account summary for the authenticated user."""
    result = await db.execute(
        select(MarginAccount).where(
            MarginAccount.user_id == user_id,
            MarginAccount.execution_mode == FuturesExecutionMode.SIMULATION,
        )
    )
    acct = result.scalar_one_or_none()
    if acct is None:
        return {
            "total_margin_balance": "0",
            "available_margin": "0",
            "used_margin": "0",
            "margin_usage_pct": "0.00",
        }

    total = Decimal(str(acct.total_margin_balance))
    used = Decimal(str(acct.used_margin))
    usage_pct = (used / total * Decimal("100")).quantize(Decimal("0.01")) if total > 0 else Decimal("0.00")

    return {
        "total_margin_balance": _fmt(total),
        "available_margin": _fmt(acct.available_margin),
        "used_margin": _fmt(used),
        "margin_usage_pct": str(usage_pct),
    }
