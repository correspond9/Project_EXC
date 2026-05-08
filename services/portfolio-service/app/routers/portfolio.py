"""
portfolio.py — REST endpoints for portfolio holdings, P&L summary, P&L history.

Routes:
  GET /api/portfolio/holdings
  GET /api/portfolio/summary
  GET /api/portfolio/pnl/history?days=30
"""
import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..models.portfolio import PnlSnapshot, PortfolioHolding
from ..models.wallet import SimulationWallet
from ..redis_client import get_redis_pool

router = APIRouter()
_bearer = HTTPBearer()

_EXECUTION_MODE = "SIMULATION"


# ── Auth ─────────────────────────────────────────────────────────────────────

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


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_price(asset: str) -> Decimal:
    """Fetch last price for an asset from Redis ticker hash."""
    redis = get_redis_pool()
    raw = await redis.hget(f"ticker:{asset}USDT", "c")
    if raw:
        try:
            return Decimal(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
        except Exception:  # noqa: BLE001
            pass
    return Decimal("0")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/api/portfolio/holdings")
async def get_holdings(
    user_id: uuid.UUID = Depends(_verify_token),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    result = await db.execute(
        select(PortfolioHolding).where(
            PortfolioHolding.user_id == user_id,
            PortfolioHolding.execution_mode == _EXECUTION_MODE,
            PortfolioHolding.quantity > 0,
        )
    )
    holdings = result.scalars().all()

    out = []
    for h in holdings:
        qty = Decimal(str(h.quantity))
        avg = Decimal(str(h.average_entry_price))
        price = await _get_price(h.asset)
        value = qty * price
        unrealised = (price - avg) * qty if qty > 0 and avg > 0 else Decimal("0")

        out.append(
            {
                "asset": h.asset,
                "quantity": str(qty),
                "average_entry_price": str(avg),
                "current_price": str(price),
                "value_usdt": str(value),
                "unrealised_pnl": str(unrealised),
                "total_realised_pnl": str(h.total_realised_pnl),
                "updated_at": h.updated_at.isoformat() if h.updated_at else None,
            }
        )
    return out


@router.get("/api/portfolio/summary")
async def get_summary(
    user_id: uuid.UUID = Depends(_verify_token),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    # Holdings
    result = await db.execute(
        select(PortfolioHolding).where(
            PortfolioHolding.user_id == user_id,
            PortfolioHolding.execution_mode == _EXECUTION_MODE,
        )
    )
    holdings = result.scalars().all()

    total_realised = Decimal("0")
    total_unrealised = Decimal("0")
    total_holdings_value = Decimal("0")

    for h in holdings:
        qty = Decimal(str(h.quantity))
        avg = Decimal(str(h.average_entry_price))
        price = await _get_price(h.asset)
        total_realised += Decimal(str(h.total_realised_pnl))
        if qty > 0:
            total_unrealised += (price - avg) * qty
            total_holdings_value += qty * price

    # USDT wallet balance
    w_result = await db.execute(
        select(SimulationWallet.balance).where(
            SimulationWallet.user_id == user_id,
            SimulationWallet.currency == "USDT",
        )
    )
    usdt_balance = Decimal(str(w_result.scalar_one_or_none() or "0"))
    total_portfolio_value = total_holdings_value + usdt_balance

    # Today's P&L delta — compare with yesterday's snapshot
    yesterday = date.today() - timedelta(days=1)
    snap_result = await db.execute(
        select(PnlSnapshot).where(
            PnlSnapshot.user_id == user_id,
            PnlSnapshot.snapshot_date == yesterday,
            PnlSnapshot.execution_mode == _EXECUTION_MODE,
        )
    )
    yesterday_snap = snap_result.scalar_one_or_none()
    if yesterday_snap:
        todays_delta = total_portfolio_value - Decimal(
            str(yesterday_snap.total_portfolio_value)
        )
    else:
        todays_delta = Decimal("0")

    return {
        "total_portfolio_value": str(total_portfolio_value),
        "holdings_value": str(total_holdings_value),
        "usdt_balance": str(usdt_balance),
        "total_realised_pnl": str(total_realised),
        "total_unrealised_pnl": str(total_unrealised),
        "todays_pnl_delta": str(todays_delta),
    }


@router.get("/api/portfolio/pnl/history")
async def get_pnl_history(
    days: int = Query(default=30, ge=1, le=365),
    user_id: uuid.UUID = Depends(_verify_token),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    since = date.today() - timedelta(days=days)
    result = await db.execute(
        select(PnlSnapshot)
        .where(
            PnlSnapshot.user_id == user_id,
            PnlSnapshot.snapshot_date >= since,
            PnlSnapshot.execution_mode == _EXECUTION_MODE,
        )
        .order_by(PnlSnapshot.snapshot_date.asc())
    )
    snaps = result.scalars().all()
    return [
        {
            "date": s.snapshot_date.isoformat(),
            "total_portfolio_value": str(s.total_portfolio_value),
            "total_realised_pnl": str(s.total_realised_pnl),
            "total_unrealised_pnl": str(s.total_unrealised_pnl),
        }
        for s in snaps
    ]
