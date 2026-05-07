import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies.auth import require_admin
from ..models.user import User
from ..schemas.admin import (
    UpdateTradingModeRequest,
    UpdateUserStatusRequest,
    UserListResponse,
    UserSummary,
)

router = APIRouter(prefix="/api/admin/users", tags=["Admin — Users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    _admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, le=100),
):
    """Return a paginated list of all users."""
    offset = (page - 1) * per_page

    count_result = await db.execute(select(func.count()).select_from(User))
    total = count_result.scalar_one()

    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(per_page)
    )
    users = result.scalars().all()

    return UserListResponse(
        total=total,
        page=page,
        per_page=per_page,
        users=[UserSummary.model_validate(u) for u in users],
    )


@router.get("/{user_id}", response_model=UserSummary)
async def get_user(
    user_id: uuid.UUID,
    _admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Return a single user's detail."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserSummary.model_validate(user)


@router.put("/{user_id}/mode", response_model=UserSummary)
async def update_trading_mode(
    user_id: uuid.UUID,
    body: UpdateTradingModeRequest,
    _admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Switch a user's trading mode between SIMULATION and LIVE."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.trading_mode = body.trading_mode
    await db.commit()
    await db.refresh(user)
    return UserSummary.model_validate(user)


@router.put("/{user_id}/status", response_model=UserSummary)
async def update_user_status(
    user_id: uuid.UUID,
    body: UpdateUserStatusRequest,
    _admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Activate or suspend a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = body.is_active
    await db.commit()
    await db.refresh(user)
    return UserSummary.model_validate(user)
