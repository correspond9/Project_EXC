"""
Price alert CRUD endpoints.
"""
import uuid
from decimal import Decimal
from typing import Annotated

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..database import AsyncSessionLocal
from ..dependencies import get_current_user_id
from ..models.alerts import AlertCondition, PriceAlert

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class CreateAlertRequest(BaseModel):
    symbol: str = Field(min_length=3, max_length=20)
    condition: AlertCondition
    target_price: Decimal = Field(gt=0)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_alert(
    body: CreateAlertRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
):
    """Create a new price alert."""
    async with AsyncSessionLocal() as db:
        alert = PriceAlert(
            user_id=user_id,
            symbol=body.symbol.upper(),
            condition=body.condition,
            target_price=body.target_price,
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)

    return {
        "id": str(alert.id),
        "symbol": alert.symbol,
        "condition": alert.condition.value,
        "target_price": str(alert.target_price),
        "is_triggered": alert.is_triggered,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
    }


@router.get("")
async def list_alerts(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    active_only: bool = True,
):
    """List price alerts for the authenticated user."""
    async with AsyncSessionLocal() as db:
        q = sa.select(PriceAlert).where(PriceAlert.user_id == user_id)
        if active_only:
            q = q.where(PriceAlert.is_triggered == False)  # noqa: E712
        q = q.order_by(PriceAlert.created_at.desc())
        rows = (await db.execute(q)).scalars().all()

    return [
        {
            "id": str(a.id),
            "symbol": a.symbol,
            "condition": a.condition.value,
            "target_price": str(a.target_price),
            "is_triggered": a.is_triggered,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None,
        }
        for a in rows
    ]


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
):
    """Delete a price alert (only if it belongs to the current user)."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            sa.select(PriceAlert).where(
                PriceAlert.id == alert_id,
                PriceAlert.user_id == user_id,
            )
        )
        alert = result.scalar_one_or_none()
        if alert is None:
            raise HTTPException(status_code=404, detail="Alert not found")
        await db.delete(alert)
        await db.commit()
