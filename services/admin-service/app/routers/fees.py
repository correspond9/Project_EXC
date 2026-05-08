"""
Admin-service — Fee configuration router.
Platform-wide and per-user fee overrides.
"""
import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies.auth import require_admin
from ..models.config import FeeConfig

router = APIRouter(prefix="/api/admin/fees", tags=["Admin — Fee Config"])


class FeeConfigOut(BaseModel):
    user_id: str | None
    maker_fee: str
    taker_fee: str

    model_config = {"from_attributes": True}

    def model_post_init(self, __context) -> None:
        self.maker_fee = str(self.maker_fee)
        self.taker_fee = str(self.taker_fee)
        if self.user_id is not None:
            self.user_id = str(self.user_id)


class FeeConfigUpdate(BaseModel):
    maker_fee: Decimal
    taker_fee: Decimal


@router.get("/default", response_model=FeeConfigOut)
async def get_default_fees(
    _admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get the platform default fee configuration."""
    result = await db.execute(
        select(FeeConfig).where(FeeConfig.user_id.is_(None))
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Default fee config not found")
    return {"user_id": None, "maker_fee": str(row.maker_fee), "taker_fee": str(row.taker_fee)}


@router.put("/default", response_model=FeeConfigOut)
async def update_default_fees(
    body: FeeConfigUpdate,
    _admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update the platform default fee rates."""
    _validate_fees(body.maker_fee, body.taker_fee)
    result = await db.execute(
        select(FeeConfig).where(FeeConfig.user_id.is_(None))
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = FeeConfig(user_id=None, maker_fee=body.maker_fee, taker_fee=body.taker_fee)
        db.add(row)
    else:
        row.maker_fee = body.maker_fee
        row.taker_fee = body.taker_fee
    await db.commit()
    return {"user_id": None, "maker_fee": str(body.maker_fee), "taker_fee": str(body.taker_fee)}


@router.put("/users/{user_id}", response_model=FeeConfigOut)
async def set_user_fee_override(
    user_id: uuid.UUID,
    body: FeeConfigUpdate,
    _admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Set a per-user fee override."""
    _validate_fees(body.maker_fee, body.taker_fee)
    result = await db.execute(
        select(FeeConfig).where(FeeConfig.user_id == user_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = FeeConfig(user_id=user_id, maker_fee=body.maker_fee, taker_fee=body.taker_fee)
        db.add(row)
    else:
        row.maker_fee = body.maker_fee
        row.taker_fee = body.taker_fee
    await db.commit()
    return {"user_id": str(user_id), "maker_fee": str(body.maker_fee), "taker_fee": str(body.taker_fee)}


@router.delete("/users/{user_id}", status_code=204)
async def remove_user_fee_override(
    user_id: uuid.UUID,
    _admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Remove a per-user fee override (falls back to platform default)."""
    result = await db.execute(
        select(FeeConfig).where(FeeConfig.user_id == user_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="No fee override for this user")
    await db.delete(row)
    await db.commit()


def _validate_fees(maker: Decimal, taker: Decimal) -> None:
    if not (Decimal("0") <= maker <= Decimal("0.1")):
        raise HTTPException(status_code=400, detail="maker_fee must be between 0 and 0.1")
    if not (Decimal("0") <= taker <= Decimal("0.1")):
        raise HTTPException(status_code=400, detail="taker_fee must be between 0 and 0.1")
