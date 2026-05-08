"""
Admin-service — Market configuration router.
Allows admins to enable/disable trading pairs and set leverage limits.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, conint
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies.auth import require_admin
from ..models.config import TradingPairConfig

router = APIRouter(prefix="/api/admin/market", tags=["Admin — Market Config"])


class PairConfigUpdate(BaseModel):
    is_active: bool | None = None
    max_leverage: int | None = None


class PairConfigOut(BaseModel):
    id: str
    symbol: str
    is_active: bool
    max_leverage: int

    model_config = {"from_attributes": True}


@router.get("/pairs", response_model=list[PairConfigOut])
async def list_pairs(
    _admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all trading pair configurations."""
    result = await db.execute(select(TradingPairConfig).order_by(TradingPairConfig.symbol))
    pairs = result.scalars().all()
    return [PairConfigOut.model_validate(p) for p in pairs]


@router.patch("/pairs/{symbol}", response_model=PairConfigOut)
async def update_pair(
    symbol: str,
    body: PairConfigUpdate,
    _admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Enable/disable a trading pair or change its max leverage."""
    result = await db.execute(
        select(TradingPairConfig).where(TradingPairConfig.symbol == symbol.upper())
    )
    pair = result.scalar_one_or_none()
    if pair is None:
        raise HTTPException(status_code=404, detail="Trading pair not found")

    if body.is_active is not None:
        pair.is_active = body.is_active
    if body.max_leverage is not None:
        if body.max_leverage < 1 or body.max_leverage > 125:
            raise HTTPException(status_code=400, detail="max_leverage must be between 1 and 125")
        pair.max_leverage = body.max_leverage

    await db.commit()
    await db.refresh(pair)
    return PairConfigOut.model_validate(pair)
